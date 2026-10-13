/* global JitsiMeetExternalAPI */
(() => {
  "use strict";
  const ui = Object.fromEntries(
    ["status", "presence", "alerts", "join", "leave", "error", "conference", "direct"]
      .map(id => [id, document.getElementById(id)])
  );
  const domain = "meet.element.io";
  const room = "FreeSnakeHQ20261013Field7a83d9";
  const listenerName = "HQ alert listener";
  const callerName = "Voice caller";
  ui.direct.href = `https://${domain}/${room}#config.startAudioOnly=true&config.startWithVideoMuted=true&userInfo.displayName=%22Voice%20caller%22`;
  let api;
  let connected = false;
  let talking = false;
  let alertsEnabled = false;
  let enablingAlerts = false;
  let disconnecting = false;
  let audioContext;
  let lastAlert = 0;
  let connectTimeout;
  const participants = new Map();
  const report = message => { ui.error.textContent = message; };

  function update() {
    const soundReady = alertsEnabled && audioContext?.state === "running";
    ui.alerts.disabled = enablingAlerts || disconnecting;
    ui.alerts.setAttribute("aria-busy", String(enablingAlerts));
    ui.alerts.setAttribute("aria-pressed", String(alertsEnabled));
    ui.alerts.textContent = enablingAlerts
      ? "Enabling sound..."
      : soundReady
        ? "Alerts on / turn off"
        : alertsEnabled
          ? "Alerts paused / turn off"
          : "Enable alerts / test sound";
    const count = [...participants.values()].filter(name => name !== listenerName).length;
    ui.presence.textContent = !api
      ? "Enable alerts to wait at HQ, or join voice chat to call."
      : !connected
        ? "Connecting to the hosted conference..."
        : count
          ? `${count} ${count === 1 ? "caller" : "callers"} waiting${talking ? "" : " - join voice chat to answer!"}`
          : "No other voice callers yet.";
    ui.join.disabled = disconnecting || enablingAlerts || (!!api && !connected);
    ui.join.hidden = talking;
    ui.leave.hidden = !api;
    ui.leave.disabled = enablingAlerts || disconnecting;
    if (connected && !talking && alertsEnabled && count && Date.now() - lastAlert >= 5000) {
      if (audioContext.state !== "running") {
        report("Alert sound is suspended. Turn alerts off and on again, and keep this tab open.");
      } else {
        lastAlert = Date.now();
        beep();
      }
    }
  }

  async function unlockAudio() {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) throw new Error("This browser does not support sound alerts.");
    if (!audioContext || audioContext.state === "closed") {
      audioContext = new AudioContextClass();
      audioContext.addEventListener("statechange", update);
    }
    await audioContext.resume();
    if (audioContext.state !== "running") throw new Error("Sound is blocked. Click Enable alerts again.");
  }

  function beep() {
    for (const offset of [0, 0.3, 0.6]) {
      const oscillator = audioContext.createOscillator();
      const gain = audioContext.createGain();
      const time = audioContext.currentTime + offset;
      oscillator.frequency.value = 880;
      gain.gain.setValueAtTime(0, time);
      gain.gain.linearRampToValueAtTime(0.15, time + 0.02);
      gain.gain.linearRampToValueAtTime(0, time + 0.22);
      oscillator.connect(gain).connect(audioContext.destination);
      oscillator.start(time);
      oscillator.stop(time + 0.25);
    }
  }

  function stop(alreadyLeft = false) {
    if (disconnecting) return;
    clearTimeout(connectTimeout);
    const previous = api;
    api = undefined;
    alertsEnabled = false;
    connected = false;
    talking = false;
    participants.clear();
    disconnecting = !!previous && !alreadyLeft;
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      clearTimeout(timeout);
      previous?.dispose();
      ui.conference.replaceChildren();
      ui.conference.hidden = true;
      disconnecting = false;
      ui.status.textContent = "Disconnected. Alerts off.";
      update();
    };
    let timeout;
    if (disconnecting) {
      ui.status.textContent = "Leaving voice chat...";
      // Keep the iframe alive until the server has processed the hangup.
      previous.addListener("readyToClose", finish);
      timeout = setTimeout(finish, 5000);
      previous.executeCommand("hangup");
    } else {
      finish();
    }
    update();
  }

  function start(asCaller) {
    if (api || disconnecting) return;
    report("");
    if (typeof JitsiMeetExternalAPI === "undefined") {
      report("Conference service could not load. Use Open direct voice room below.");
      return;
    }
    talking = asCaller;
    ui.conference.hidden = false;
    ui.status.textContent = "Connecting to hosted voice room...";
    try {
      api = new JitsiMeetExternalAPI(domain, {
        roomName: room,
        parentNode: ui.conference,
        width: "100%",
        height: "100%",
        userInfo: { displayName: asCaller ? callerName : listenerName },
        configOverwrite: {
          prejoinConfig: { enabled: false },
          startAudioOnly: true,
          startWithAudioMuted: !asCaller,
          startWithVideoMuted: true,
          disableInitialGUM: !asCaller,
          p2p: { enabled: false },
          disableDeepLinking: true,
          enableWelcomePage: false,
          toolbarButtons: ["microphone", "hangup", "settings"],
          hideConferenceSubject: true
        }
      });
    } catch (error) {
      stop();
      report(`Could not open conference: ${error.message}. Use Open direct voice room.`);
      return;
    }
    const current = api;
    connectTimeout = setTimeout(() => {
      if (api === current && !connected) {
        stop();
        report("Conference has not connected. Use Open direct voice room below, or switch between Wi-Fi and mobile data.");
      }
    }, 30000);
    current.addListener("videoConferenceJoined", joined => {
      if (api !== current) return;
      clearTimeout(connectTimeout);
      connected = true;
      report("");
      ui.status.textContent = talking
        ? "In voice chat. Check the microphone button below; unmute it to talk."
        : "HQ listening with microphone off. Alerts enabled; incoming speech can also be heard.";
      for (const participant of current.getParticipantsInfo()) {
        if (participant.participantId !== joined.id) {
          participants.set(participant.participantId, participant.displayName);
        }
      }
      update();
    });
    current.addListener("participantJoined", participant => {
      if (api !== current) return;
      participants.set(participant.id, participant.displayName);
      update();
    });
    current.addListener("participantLeft", participant => {
      if (api !== current) return;
      participants.delete(participant.id);
      update();
    });
    current.addListener("displayNameChange", participant => {
      if (api !== current || !participants.has(participant.id)) return;
      participants.set(participant.id, participant.displayname);
      update();
    });
    current.addListener("audioMuteStatusChanged", event => {
      if (api !== current) return;
      if (connected && !event.muted && !talking) {
        talking = true;
        current.executeCommand("displayName", callerName);
      }
      if (connected) {
        ui.status.textContent = talking
          ? `In voice chat - microphone ${event.muted ? "muted" : "enabled"}.`
          : "HQ listening with microphone off. Waiting for callers.";
      }
      update();
    });
    current.addListener("videoConferenceLeft", () => {
      if (api === current) stop(true);
    });
    current.addListener("errorOccurred", event => {
      if (api !== current) return;
      if (event.isFatal) {
        stop();
        ui.status.textContent = "Conference connection failed. Rejoin or use the direct room.";
      }
      report(`Conference error: ${event.message || event.name || event.type || "connection failed"}. Use Open direct voice room if it does not recover.`);
    });
    update();
  }

  ui.alerts.onclick = async () => {
    if (enablingAlerts || disconnecting) return;
    if (alertsEnabled) {
      alertsEnabled = false;
      report("");
      if (!talking) stop();
      update();
      return;
    }
    enablingAlerts = true;
    update();
    try {
      await unlockAudio();
      alertsEnabled = true;
      report("");
      beep();
      if (!api) start(false);
    } catch (error) { report(error.message); }
    finally {
      enablingAlerts = false;
      update();
    }
  };
  ui.join.onclick = async () => {
    if (disconnecting || enablingAlerts || talking) return;
    if (!api) {
      start(true);
      return;
    }
    if (!connected) return;
    const current = api;
    talking = true;
    update();
    try {
      const muted = await current.isAudioMuted();
      if (api !== current) return;
      current.executeCommand("displayName", callerName);
      if (muted) current.executeCommand("toggleAudio");
      ui.status.textContent = "In voice chat. Allow microphone access and unmute below to talk.";
    } catch (error) {
      if (api === current) {
        talking = false;
        report(`Could not enable microphone: ${error.message}`);
        update();
      }
    }
  };
  ui.leave.onclick = () => stop();
  setInterval(update, 1000);
  document.addEventListener("visibilitychange", update);
  window.addEventListener("pagehide", () => stop());
  ui.status.textContent = "Ready. Choose Enable alerts at HQ, or Join voice chat in the field.";
  update();
})();
