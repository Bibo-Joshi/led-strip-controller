const baseUrl = window.location.protocol + "//" + window.location.host;
const apiUrl = baseUrl + "/api";
const WSocket = new WebSocket("ws://" + window.location.host + "/ws");

function exists(element) {
  return typeof element != "undefined" && element != null;
}

deleteAlarm = function (alarmID) {
  const alarmElement = document.getElementById(alarmID);
  if (!exists(alarmElement)) {
    return;
  }
  alarmElement.remove();
};

deleteAlarmEventListener = function (uid) {
  WSocket.send(
    JSON.stringify({
      deleteAlarm: uid,
    }),
  );
  deleteAlarm(uid);
};
