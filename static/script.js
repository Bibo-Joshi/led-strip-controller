const values = document.getElementById("values");
const hexInput = document.getElementById("hexInput");
const baseUrl = window.location.protocol + '//' + window.location.host
const apiUrl = baseUrl + '/api';
const WSocket = new WebSocket('ws://' + window.location.host + '/ws');
const powerToggle = document.getElementById('power-toggle');
const backgroundElement = document.getElementById('body');
const rgbRegex = /rgb\((\d{1,3}), (\d{1,3}), (\d{1,3})\)/;
const radioButtons = document.forms["static-picker"].elements["color"];

function rgbAverage(color1, color2) {
    return {
        r: (color1.red + color2.red) / 2,
        g: (color1.green + color2.green) / 2,
        b: (color1.blue + color2.blue) / 2
    };
}

function rgbToHex(rgb) {
    return "#" + ((1 << 24) + (rgb.r << 16) + (rgb.g << 8) + rgb.b).toString(16).slice(1);
}

function updateBackgroundColor(color, other_picker) {
    let newRGB;
    if (other_picker.color.value === 0) {
        newRGB = color.rgb;
    } else {
        if (color.value > 0) {
            newRGB = rgbAverage(color, other_picker.color);
        } else {
            newRGB = other_picker.color.rgb;
        }
    }

    backgroundElement.style.backgroundColor = rgbToHex(newRGB);
}

const RGBPicker = new iro.ColorPicker(".RGBPicker", {
    // color picker options
    // Option guide: https://iro.js.org/guide.html#color-picker-options
    width: 280,
    color: "rgb(0,0,0)",
    borderWidth: 1,
    borderColor: "#fff",
});
const WWPicker = new iro.ColorPicker(".WWPicker", {
    width: 280,
    color: "rgb(0, 0, 0)",
    borderWidth: 1,
    borderColor: "#fff",
    layout: [
        {
            component: iro.ui.Slider,
            options: {
                // can also be 'saturation', 'value', 'red', 'green', 'blue', 'alpha' or 'kelvin'
                sliderType: 'value'
            }
        },
    ]
});

for (const radio of radioButtons) {
    radio.onclick = function () {
        // It would probably be better to encode the color value in the html tag somehow but
        // I'm in no mood to learn how to build that and this solution is better than having
        // to adjust the html each time the colors are updated
        const match = rgbRegex.exec(window.getComputedStyle(radio).getPropertyValue('color'));
        console.log(parseInt(match[1]), typeof  parseInt(match[1]));
        if (match !== null) {
            RGBPicker.color.red = parseInt(match[1]);
            RGBPicker.color.green = parseInt(match[2]);
            RGBPicker.color.blue = parseInt(match[3]);

            WWPicker.color.value = 0;
            WSocket.send(JSON.stringify({updateWhite: 0}));
            WSocket.send(JSON.stringify({
                updateRGB: {
                    red: RGBPicker.color.red,
                    green: RGBPicker.color.green,
                    blue: RGBPicker.color.blue
                }
            }));
        }

    }
}

fetch(apiUrl + '/status',
    {
        headers: {"Content-Type": "application/json"},
        method: "GET"
    }).then((response) => {
    if (response.ok) {
        return response.json()
    } else {
        console.log('Could not get current color: ' + response.statusText)
    }
}).then((json) => {
    powerToggle.checked = json;
});
powerToggle.addEventListener("click", function () {
    WSocket.send(JSON.stringify({updateStatus: this.checked}));
})

function current_rgb_color(colorPicker) {
    fetch(apiUrl + '/color',
        {
            headers: {"Content-Type": "application/json"},
            method: "GET"
        }).then((response) => {
        if (response.ok) {
            return response.json()
        } else {
            console.log('Could not get current color: ' + response.statusText)
        }
    }).then((json) => {
        colorPicker.red = json['red'];
        colorPicker.green = json['green'];
        colorPicker.blue = json['blue'];
    })
}

function current_white_color(colorPicker) {
    fetch(apiUrl + '/color',
        {
            headers: {"Content-Type": "application/json"},
            method: "GET"
        }).then((response) => {
        if (response.ok) {
            return response.json()
        } else {
            console.log('Could not get current color: ' + response.statusText)
        }
    }).then((json) => {
        colorPicker.value = json['white'];
    })
}

function uncheckStaticPicker() {
    for (const radio of radioButtons) {
        radio.checked = false;
    }
}

RGBPicker.on("color:init", current_rgb_color);
WWPicker.on("color:init", current_white_color);

RGBPicker.on(["color:init", "color:change"], function (color) {
    // Show the current color in different formats
    // Using the selected color: https://iro.js.org/guide.html#selected-color-api
    values.innerHTML = [
        "hex: " + color.hexString,
        "rgb: " + color.rgbString,
        "hsl: " + color.hslString].join("<br>");

    hexInput.value = color.hexString;

    updateBackgroundColor(color, WWPicker);
    // if (WWPicker.color.value === 0) {
    //     backgroundElement.style.backgroundColor = color.hexString;
    // } else {
    //     if (color.value > 0) {
    //         backgroundElement.style.backgroundColor = colorAverage(color, WWPicker.color);
    //     } else {
    //         backgroundElement.style.backgroundColor = WWPicker.color.hexString;
    //     }
    // }
});
WWPicker.on("color:change", function (color) {
    updateBackgroundColor(color, RGBPicker);
});

RGBPicker.on('input:change', function (color) {
    if (WSocket.readyState !== WSocket.OPEN) {
        alert('No connection to server. Color change will not propagate.');
        return;
    }
    WSocket.send(JSON.stringify({
        updateRGB: {
            red: color.red,
            green: color.green,
            blue: color.blue
        }
    }));
    uncheckStaticPicker();
});
WWPicker.on('input:change', function (color) {
    if (WSocket.readyState !== WSocket.OPEN) {
        alert('No connection to server. Color change will not propagate.');
        return;
    }
    WSocket.send(JSON.stringify({updateWhite: color.value}));
    uncheckStaticPicker();
});

WSocket.onmessage = function (event) {
    const jsonData = JSON.parse(event.data);
    if (jsonData.updateRGB !== undefined) {
        RGBPicker.color.red = jsonData.updateRGB.red;
        RGBPicker.color.green = jsonData.updateRGB.green;
        RGBPicker.color.blue = jsonData.updateRGB.blue;
        uncheckStaticPicker();
    } else if (jsonData.updateWhite !== undefined) {
        WWPicker.color.value = jsonData.updateWhite;
        uncheckStaticPicker();
    } else if (jsonData.updateStatus !== undefined) {
        powerToggle.checked = jsonData.updateStatus;
    }
}
WSocket.onclose = function (event) {
    console.log(event.toString());
    alert('Lost connection to server. Please reload the page.')
}
WSocket.onerror = function (event) {
    console.log(event.toString());
    alert('Error in connection to server. Please reload the page.')
}

hexInput.addEventListener('change', function () {
    RGBPicker.color.hexString = this.value;
});