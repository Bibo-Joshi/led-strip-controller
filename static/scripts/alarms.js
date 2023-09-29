const alarms = document.getElementsByClassName("Alarm");
const time_pickers = new Map();

const activeToggleEventListener = function () {
  const alarms = document.getElementsByClassName("Alarm");
  WSocket.send(
    JSON.stringify({
      editAlarm: {
        uid: this.id.toString().slice(0, -7),
        editedAlarm: { active: this.checked },
      },
    }),
  );
};

const addDayToggleEventListeners = function (dayToggles, uid) {
  dayToggles.forEach((element, day) => {
    element.addEventListener("click", function () {
      const activeDays = [];
      dayToggles.forEach((e, d) => {
        if (e.checked) {
          activeDays.push(d);
        }
      });
      WSocket.send(
        JSON.stringify({
          editAlarm: {
            uid: uid,
            editedAlarm: { weekdays: activeDays },
          },
        }),
      );
    });
  });
};

const addDeleteButtonEventListener = function (deleteButton, uid) {
  deleteButton.addEventListener("click", function () {
    deleteAlarmEventListener(uid);
  });
};

const addTimePicker = function (uid, hour, minute, type) {
  let element_id = uid + "-" + type;
  let picker = new AirDatepicker("#" + element_id, {
    locale: localeDe,
    isMobile: true,
    timepicker: true,
    onlyTimepicker: true,
    timeFormat: "HH:mm",
    minutesStep: 5,
    startDate: new Date(2023, 1, 1, hour, minute),
    buttons: [
      {
        content: "Abbruch",
        onClick: function (picker) {
          picker.hide();
        },
      },
      {
        content: "Fertig",
        onClick: function (picker) {
          picker.hide();
          let hour = String(picker.selectedDates[0].getHours()).padStart(
            2,
            "0",
          );
          let minute = String(picker.selectedDates[0].getMinutes()).padStart(
            2,
            "0",
          );
          let effect_data = {};
          effect_data[type] = hour + ":" + minute;
          WSocket.send(
            JSON.stringify({
              editAlarm: {
                uid: uid,
                editedAlarm: { effect: effect_data },
              },
            }),
          );
        },
      },
    ],
  });
  time_pickers.set(element_id, picker);
};

for (const alarm of alarms) {
  // On-Off toggle
  const activeToggle = document.getElementById(alarm.id + "-active");
  activeToggle.addEventListener("click", activeToggleEventListener);

  // Day toggles
  const dayToggles = new Map();
  for (let day = 0; day <= 6; day++) {
    dayToggles.set(day, document.getElementById(alarm.id + "-" + day));
  }
  addDayToggleEventListeners(dayToggles, alarm.id);

  // Delete button
  const deleteButton = document.getElementById(alarm.id + "-delete");
  addDeleteButtonEventListener(deleteButton, alarm.id);

  // Time pickers
  for (const picker_suffix of ["start", "end", "off"]) {
    let time = document.getElementById(alarm.id + "-" + picker_suffix).value;
    let hour = parseInt(time.slice(0, 2));
    let minute = parseInt(time.slice(3, 5));
    addTimePicker(alarm.id, hour, minute, picker_suffix);
  }
}
