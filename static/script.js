// Create a new color picker instance
// https://iro.js.org/guide.html#getting-started
var RGBPicker = new iro.ColorPicker(".RGBPicker", {
    // color picker options
    // Option guide: https://iro.js.org/guide.html#color-picker-options
    width: 280,
    color: "rgb(255, 0, 0)",
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


const values = document.getElementById("values");
const hexInput = document.getElementById("hexInput");
const baseUrl = window.location.protocol + '//' + window.location.host
const apiUrl = baseUrl + '/api';
const wsUrl = 'ws://' + window.location.host + '/ws';
const RGBWebSocket = new WebSocket(wsUrl + '/rgb')
const WWWebSocket = new WebSocket(wsUrl + '/white')

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

RGBPicker.on("color:init", current_rgb_color);
WWPicker.on("color:init", current_white_color);

// https://iro.js.org/guide.html#color-picker-events
RGBPicker.on(["color:init", "input:change"], function (color) {
    // Show the current color in different formats
    // Using the selected color: https://iro.js.org/guide.html#selected-color-api
    values.innerHTML = [
        "hex: " + color.hexString,
        "rgb: " + color.rgbString,
        "hsl: " + color.hslString].join("<br>");

    hexInput.value = color.hexString;
});

RGBPicker.on('input:change', function (color) {
    if (RGBWebSocket.readyState !== WebSocket.OPEN) {
        alert('No connection to server. Color change will not propagate.');
        return;
    }
    RGBWebSocket.send(JSON.stringify({red: color.red, green: color.green, blue: color.blue}));
});
RGBWebSocket.onmessage = function (event) {
    const jsonData = JSON.parse(event.data);
    RGBPicker.color.red = jsonData.red;
    RGBPicker.color.green = jsonData.green;
    RGBPicker.color.blue = jsonData.blue;
}

WWPicker.on('input:change', function (color) {
    if (RGBWebSocket.readyState !== WebSocket.OPEN) {
        alert('No connection to server. Color change will not propagate.');
        return;
    }
    WWWebSocket.send(JSON.stringify({white: color.value}));
});
WWWebSocket.onmessage = function (event) {
    const jsonData = JSON.parse(event.data);
    WWPicker.color.value = jsonData.white;
}

RGBWebSocket.onclose = function (event) {
    alert('Lost connection to server. Please reload the page.')
}
RGBWebSocket.onerror = function (event) {
    alert('Error in connection to server. Please reload the page.')
}
WWWebSocket.onclose = function (event) {
    alert('Lost connection to server. Please reload the page.')
}
WWWebSocket.onerror = function (event) {
    alert('Error in connection to server. Please reload the page.')
}

hexInput.addEventListener('change', function () {
    RGBPicker.color.hexString = this.value;
});