const alarms = document.getElementsByClassName("Alarm");

const activeToggleEventListener = function () {
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
}
