WSocket.onclose = function (event) {
  console.log(event.toString());
  alert("Lost connection to server. Please reload the page.");
};
WSocket.onerror = function (event) {
  console.log(event.toString());
  alert("Error in connection to server. Please reload the page.");
};

const formatTime = function (time_str) {
  if (time_str.endsWith(":00")) {
    return time_str.slice(0, 5);
  } else {
    return time_str;
  }
};
const timesMap = new Map();
timesMap.set("start", "mi-sunrise-1");
timesMap.set("end", "mi-sun");
timesMap.set("off", "mi-sunset");

WSocket.onmessage = function (event) {
  const jsonData = JSON.parse(event.data);
  if (jsonData.updateRGB !== undefined) {
    RGBPicker.color.red = jsonData.updateRGB.red;
    RGBPicker.color.green = jsonData.updateRGB.green;
    RGBPicker.color.blue = jsonData.updateRGB.blue;
    uncheckStaticPicker();
  } else if (jsonData.updateWhite !== undefined) {
    WWPicker.color.value = Math.round((jsonData.updateWhite * 100) / 255);
    uncheckStaticPicker();
  } else if (jsonData.updateColor !== undefined) {
    RGBPicker.color.red = jsonData.updateColor.red;
    RGBPicker.color.green = jsonData.updateColor.green;
    RGBPicker.color.blue = jsonData.updateColor.blue;
    WWPicker.color.value = Math.round((jsonData.updateColor.white * 100) / 255);
    uncheckStaticPicker();
  } else if (jsonData.updateStatus !== undefined) {
    powerToggle.checked = jsonData.updateStatus;
  } else if (jsonData.setAlarm !== undefined) {
    let setAlarm = JSON.parse(jsonData.setAlarm);
    const alarmElement = document.getElementById(setAlarm.uid);
    if (exists(alarmElement)) {
      const activeToggle = document.getElementById(alarmElement.id + "-active");
      activeToggle.checked = setAlarm.active;

      timesMap.forEach((icon, key) => {
        const input = document.getElementById(alarmElement.id + "-" + key);
        input.value = formatTime(setAlarm.effect[key]);
        let hour = parseInt(setAlarm.effect[key].split(":")[0]);
        let minute = parseInt(setAlarm.effect[key].split(":")[1]);
        time_pickers
          .get(setAlarm.uid + "-" + key)
          .selectDate(new Date(2023, 9, 29, hour, minute));
      });

      for (let day = 0; day <= 6; day++) {
        const dayToggle = document.getElementById(alarmElement.id + "-" + day);
        dayToggle.checked = setAlarm.weekdays.includes(day);
      }
    } else {
      addAlarm(setAlarm);
    }
  } else if (jsonData.deleteAlarm !== undefined) {
    deleteAlarm(jsonData.deleteAlarm);
  }
};

deleteAlarm = function (alarmID) {
  const alarmElement = document.getElementById(alarmID);
  if (!exists(alarmElement)) {
    return;
  }
  alarmElement.remove();
};

addAlarm = function (alarm) {
  const alarmID = alarm.uid;
  let alarms_element = document.getElementsByClassName("Alarms")[0];
  const toggle = document.createElement("input");
  toggle.type = "checkbox";
  toggle.className = "active-checkbox";
  toggle.id = alarmID + "-active";
  toggle.checked = true;
  toggle.addEventListener("click", activeToggleEventListener);
  const new_alarm = document.createElement("div");
  new_alarm.className = "Alarm";
  new_alarm.id = alarmID;
  new_alarm.name = "alarm";
  alarms_element.appendChild(toggle);
  alarms_element.appendChild(new_alarm);

  const alarm_times = document.createElement("div");
  alarm_times.className = "Alarm__times";
  new_alarm.appendChild(alarm_times);
  const map = new Map();
  timesMap.forEach((icon, key) => {
    const time_div = document.createElement("div");
    time_div.className = "Alarm__" + key;
    const i = document.createElement("i");
    i.className = icon;

    const input = document.createElement("input");
    input.className = "no-select, TimePicker";
    input.value = formatTime(alarm.effect[key]);
    input.id = alarmID + "-" + key;
    input.readOnly = true;
    let hour = parseInt(alarm.effect[key].split(":")[0]);
    let minute = parseInt(alarm.effect[key].split(":")[1]);

    time_div.appendChild(i);
    time_div.appendChild(input);
    alarm_times.appendChild(time_div);

    addTimePicker(alarmID, hour, minute, key);
  });

  const delete_div = document.createElement("div");
  delete_div.className = "Alarm__delete";
  const delete_button = document.createElement("button");
  delete_button.className = "Alarm__delete__button";
  delete_button.id = alarmID + "-delete";
  delete_button.addEventListener("click", function () {
    deleteAlarmEventListener(alarmID);
  });
  const delete_icon = document.createElement("i");
  delete_icon.className = "mi-delete";
  delete_button.appendChild(delete_icon);
  delete_div.appendChild(delete_button);
  alarm_times.appendChild(delete_div);

  const next_row = document.createElement("div");
  next_row.className = "Alarm__second_row";
  new_alarm.appendChild(next_row);
  const w_days = document.createElement("div");
  w_days.className = "Alarm__weekdays";
  next_row.appendChild(w_days);
  const weekdays = new Map();
  const dayToggles = new Map();
  weekdays.set(1, "Mo");
  weekdays.set(2, "Di");
  weekdays.set(3, "Mi");
  weekdays.set(4, "Do");
  weekdays.set(5, "Fr");
  weekdays.set(6, "Sa");
  weekdays.set(0, "So");
  weekdays.forEach((name, day) => {
    const div = document.createElement("div");
    div.className = "Alarm__day";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = "None";
    input.id = alarmID + "-" + day;
    input.checked = alarm.weekdays.includes(day);
    const label = document.createElement("label");
    label.className = "Alarm__day__label";
    label.htmlFor = alarmID + "-" + day;
    label.textContent = name;
    div.appendChild(input);
    div.appendChild(label);
    w_days.appendChild(div);
    dayToggles.set(day, input);
  });
  addDayToggleEventListeners(dayToggles, alarmID);

  const lb_toggle = document.createElement("label");
  lb_toggle.className = "lb-toggle";
  lb_toggle.htmlFor = alarmID + "-active";
  next_row.appendChild(lb_toggle);
};
