(() => {
  const params = new URLSearchParams(location.search);
  const videoId = params.get('video') || '';
  const start = Number(params.get('start'));
  const end = Number(params.get('end'));
  const title = params.get('title') || 'Council discussion';
  const range = params.get('range') || '';
  const returnPath = params.get('return') || '';
  const panel = document.querySelector('.dossier-video-panel');
  let player;
  let boundaryTimer;

  const valid = /^[\w-]{11}$/.test(videoId) && Number.isFinite(start) && Number.isFinite(end) && start >= 0 && end > start;
  const showError = () => {
    window.clearInterval(boundaryTimer);
    panel.innerHTML = '<div><p class="pdf-error">The bounded video could not be loaded.</p></div>';
  };
  if (!valid) {
    document.querySelector('#video-title').textContent = 'Video segment not found';
    document.querySelector('#video-description').textContent = 'The requested segment is invalid.';
    showError();
    return;
  }

  document.title = `${title} | Beaumont Intelligence`;
  document.querySelector('#video-title').textContent = title;
  document.querySelector('#video-description').textContent = `Playback is limited to ${range}.`;
  document.querySelector('#video-end-time').textContent = range.split('–')[1] || 'the verified endpoint';
  if (/^[\w.-]+\.html(?:#[\w-]*)?$/.test(returnPath)) document.querySelector('#video-return').href = returnPath;

  const enforceBoundary = () => {
    if (!player || typeof player.getCurrentTime !== 'function') return;
    if (player.getCurrentTime() >= end - 0.15) {
      player.pauseVideo();
      player.seekTo(end - 0.2, true);
    }
  };
  window.onYouTubeIframeAPIReady = () => {
    player = new YT.Player('bounded-video', {
      videoId,
      width: '960',
      height: '540',
      playerVars: { autoplay: 1, start, end, playsinline: 1, rel: 0 },
      events: {
        onReady: event => {
          event.target.seekTo(start, true);
          event.target.playVideo();
          boundaryTimer = window.setInterval(enforceBoundary, 200);
        },
        onStateChange: enforceBoundary,
        onError: showError
      }
    });
  };
  const api = document.createElement('script');
  api.src = 'https://www.youtube.com/iframe_api';
  api.onerror = showError;
  document.head.appendChild(api);
})();
