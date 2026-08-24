(() => {
  const toSeconds = value => {
    const parts = value.split(':').map(Number);
    if (parts.some(Number.isNaN) || parts.length < 2 || parts.length > 3) return null;
    return parts.reduce((total, part) => total * 60 + part, 0);
  };
  const meetingVideo = [...document.querySelectorAll('a[href*="youtube.com/watch"]')].map(link => {
    try { return new URL(link.href).searchParams.get('v'); } catch { return null; }
  }).find(Boolean);
  if (!meetingVideo) return;

  document.querySelectorAll('.agenda-item .after-grid').forEach(summary => {
    const videoValue = [...summary.querySelectorAll('div')].find(item => item.querySelector('strong')?.textContent.trim() === 'Video')?.querySelector('span');
    if (!videoValue || videoValue.querySelector('a')) return;
    const match = videoValue.textContent.match(/(\d{1,2}:\d{2}(?::\d{2})?)\s*[·–-]\s*Vote\s+(\d{1,2}:\d{2}(?::\d{2})?)/i);
    if (!match) return;
    const start = toSeconds(match[1]);
    const vote = toSeconds(match[2]);
    if (start === null || vote === null || vote < start) return;

    const clip = document.createElement('div');
    clip.className = 'briefing-video-clip';
    clip.innerHTML = `<div class="briefing-video-frame"><iframe src="https://www.youtube-nocookie.com/embed/${meetingVideo}?start=${start}&end=${vote + 15}&rel=0" title="Council discussion video from ${match[1]} through 15 seconds after the ${match[2]} vote" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div><p>Discussion ${match[1]} · Vote ${match[2]} · Clip ends 15 seconds after the vote</p>`;
    summary.insertAdjacentElement('afterend', clip);
  });
})();
