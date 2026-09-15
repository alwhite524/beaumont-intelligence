const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.style = {}; this.attrs = {}; this.events = {}; this.clientWidth = 360; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute(k, v) { this.attrs[k] = v; }
  removeAttribute(k) { delete this.attrs[k]; }
  addEventListener(k, v) { this.events[k] = v; }
  before(marker) { this.marker = marker; }
  replaceWith(element) { this.replacement = element; }
  remove() { this.removed = true; }
  showModal() { this.open = true; }
  close() { this.open = false; this.events.close?.(); }
  focus() {}
  getContext() { return {}; }
  querySelectorAll(tag) { return this.children.flatMap(c => [...(c.tag === tag ? [c] : []), ...c.querySelectorAll(tag)]); }
}
function setup(fail = false) {
  let destroyed = 0;
  const requested = [];
  const lib = {
    GlobalWorkerOptions: {},
    getDocument: () => ({ destroy: async () => { destroyed++; }, promise: fail ? Promise.reject(new Error('blocked host')) : Promise.resolve({
      numPages: 1000,
      getPage: async number => {
        requested.push(number);
        return { getViewport: ({ scale }) => ({ width: 600 * scale, height: 800 * scale }), render: () => ({ promise: Promise.resolve(), cancel() {} }), cleanup() {} };
      }
    }) })
  };
  const source = fs.readFileSync('docs/documents/pdf-reader.js', 'utf8').replace(/import\('https:[^']+'\)/, 'Promise.resolve(mockLibrary)');
  const document = { body: new Element('body'), createElement: tag => new Element(tag), addEventListener() {}, removeEventListener() {} };
  const context = { window: { devicePixelRatio: 3 }, document, mockLibrary: lib, console: { error() {} } };
  vm.runInNewContext(source, context);
  return { reader: context.window.BIPdfReader, container: new Element('div'), requested, document, destroyed: () => destroyed };
}
test('renders one page of a large document and respects policy ranges', async () => {
  const { reader, container, requested } = setup();
  await reader.open(container, '/policy.pdf', 'Policy', { startPage: 400, endPage: 410 });
  assert.deepEqual(requested, [400]);
  let canvas = container.querySelectorAll('canvas')[0];
  assert.ok(canvas.width * canvas.height <= 2000000);
  const buttons = container.querySelectorAll('button');
  assert.equal(buttons[0].disabled, true);
  await buttons[1].events.click();
  assert.deepEqual(requested, [400, 401]);
  assert.equal(container.querySelectorAll('canvas').length, 1);
  assert.equal(canvas.width, 0);
});
test('blocked PDF retains an actionable original link and clears busy state', async () => {
  const { reader, container } = setup(true);
  await reader.open(container, 'https://example.org/report.pdf', 'Report');
  assert.equal(container.querySelectorAll('a')[0].href, 'https://example.org/report.pdf');
  assert.match(container.querySelectorAll('p')[0].textContent, /Inline viewing is unavailable/);
  assert.equal(container.attrs['aria-busy'], undefined);
});
test('close releases the PDF session', async () => {
  const { reader, container, destroyed } = setup();
  await reader.open(container, '/report.pdf', 'Report');
  reader.clear(container);
  assert.equal(destroyed(), 1);
  assert.equal(container.children.length, 0);
});

test('fullscreen fallback restores the viewer on exit and close', async () => {
  const { reader, container, document } = setup();
  container.style.cssText = 'width:360px';
  await reader.open(container, '/report.pdf', 'Report');
  const toggle = container.querySelectorAll('button')[2];
  await toggle.events.click();
  const dialog = document.body.children[0];
  assert.equal(dialog.open, true);
  assert.equal(toggle.textContent, 'Exit full screen');
  dialog.close();
  assert.equal(container.marker.replacement, container);
  assert.equal(container.style.cssText, 'width:360px');
  assert.equal(toggle.attrs['aria-pressed'], 'false');
  await toggle.events.click();
  reader.clear(container);
  assert.equal(document.body.children[1].removed, true);
});

