(() => {
  const VIDEO_ID = "pJere8tXO7M";
  const START_SECONDS = 14901;
  const END_SECONDS = 15216;
  const panel = document.querySelector(".dossier-video-panel");
  let player;
  let boundaryTimer;

  const showError = () => {
    window.clearInterval(boundaryTimer);
    panel.innerHTML = '<div><p class="pdf-error">The bounded video could not be loaded.</p></div>';
  };

  const enforceBoundary = () => {
    if (!player || typeof player.getCurrentTime !== "function") return;
    if (player.getCurrentTime() >= END_SECONDS - 0.15) {
      player.pauseVideo();
      player.seekTo(END_SECONDS - 0.2, true);
    }
  };

  window.onYouTubeIframeAPIReady = () => {
    player = new YT.Player("bounded-video", {
      videoId: VIDEO_ID,
      width: "960",
      height: "540",
      playerVars: {
        autoplay: 1,
        start: START_SECONDS,
        end: END_SECONDS,
        playsinline: 1,
        rel: 0
      },
      events: {
        onReady: (event) => {
          event.target.seekTo(START_SECONDS, true);
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
