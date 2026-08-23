(() => {
  const segments = {
    retention: { videoId: "jsKvsxMHhzM", start: 16594, end: 16703, title: "Retention legislation discussed", date: "April 5, 2022", range: "4:36:34–4:38:23" },
    encroachment: { videoId: "I22ZvW6YwsQ", start: 705, end: 745, title: "Installation authority expands citywide", date: "May 2, 2023", range: "11:45–12:25" },
    flock: { videoId: "pJere8tXO7M", start: 14901, end: 15216, title: "Flock camera expansion", date: "August 20, 2024", range: "4:08:21–4:13:36" },
    axon: { videoId: "cfqIZpAQfg4", start: 11176, end: 11910, title: "Five-year Axon ecosystem approved", date: "December 2, 2025", range: "3:06:16–3:18:30" },
    drone: { videoId: "f0e7yqc3XYs", start: 10461, end: 11387, title: "Drone-as-First-Responder agreement approved", date: "April 7, 2026", range: "2:54:21–3:09:47" },
    peregrine: { videoId: "WnQ5OtILrzU", start: 4434, end: 4670, title: "Peregrine platform discussed and approved", date: "August 4, 2026", range: "1:13:54–1:17:50" }
  };
  const segmentId = new URLSearchParams(window.location.search).get("segment") || "flock";
  const segment = segments[segmentId];
  const panel = document.querySelector(".dossier-video-panel");
  let player;
  let boundaryTimer;

  const showError = () => {
    window.clearInterval(boundaryTimer);
    panel.innerHTML = '<div><p class="pdf-error">The bounded video could not be loaded.</p></div>';
  };

  const enforceBoundary = () => {
    if (!player || typeof player.getCurrentTime !== "function") return;
    if (player.getCurrentTime() >= segment.end - 0.15) {
      player.pauseVideo();
      player.seekTo(segment.end - 0.2, true);
    }
  };

  if (!segment) {
    document.querySelector("#video-title").textContent = "Video segment not found";
    document.querySelector("#video-description").textContent = "The requested segment is not part of this dossier.";
    showError();
    return;
  }

  document.title = `${segment.title} | Moving Beaumont Forward`;
  document.querySelector("#video-title").textContent = segment.title;
  document.querySelector("#video-description").textContent = `${segment.date} · Playback is limited to ${segment.range}.`;
  document.querySelector("#video-end-time").textContent = segment.range.split("–")[1];

  window.onYouTubeIframeAPIReady = () => {
    player = new YT.Player("bounded-video", {
      videoId: segment.videoId,
      width: "960",
      height: "540",
      playerVars: {
        autoplay: 1,
        start: segment.start,
        end: segment.end,
        playsinline: 1,
        rel: 0
      },
      events: {
        onReady: (event) => {
          event.target.seekTo(segment.start, true);
          event.target.playVideo();
          boundaryTimer = window.setInterval(enforceBoundary, 200);
        },
        onStateChange: enforceBoundary,
        onError: showError
      }
    });
  };

  const api = document.createElement("script");
  api.src = "https://www.youtube.com/iframe_api";
  api.onerror = showError;
  document.head.appendChild(api);
})();
