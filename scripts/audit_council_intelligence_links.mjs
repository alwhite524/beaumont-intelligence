/** Verify Council Intelligence document, video, and rendered-page sources. */

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";


const root = path.resolve(import.meta.dirname, "..");
const docsRoot = path.join(root, "docs");
const dataPath = path.join(docsRoot, "documents", "document-data.js");
const briefingRoot = path.join(docsRoot, "briefings");
const concurrency = 8;

const dataSource = await fs.readFile(dataPath, "utf8");
const documentLibrary = new Function(`${dataSource}\nreturn documentLibrary;`)();

const htmlFiles = [
  "council-intelligence.html",
  "council-briefings-2026.html",
  ...(await fs.readdir(briefingRoot))
    .filter((name) => name.endsWith(".html"))
    .map((name) => path.join("briefings", name)),
];

const videoUrls = new Set();
for (const relative of htmlFiles) {
  const source = await fs.readFile(path.join(docsRoot, relative), "utf8");
  for (const match of source.matchAll(/https:\/\/(?:www\.)?youtube\.com\/watch\?[^"'\s<]+/g)) {
    videoUrls.add(match[0].replaceAll("&amp;", "&"));
  }
}

const documentUrls = new Set(documentLibrary.map((record) => record.pdf));
const localImages = documentLibrary.flatMap((record) =>
  (record.pageImages || []).map((image) => ({ id: record.id, image })),
);

const failures = [];
for (const { id, image } of localImages) {
  const absolute = path.resolve(path.dirname(path.join(docsRoot, "documents", "viewer.html")), image);
  try {
    const stat = await fs.stat(absolute);
    if (!stat.isFile() || stat.size === 0) failures.push(`${id}: invalid rendered page ${image}`);
  } catch {
    failures.push(`${id}: missing rendered page ${image}`);
  }
}

const remoteChecks = [
  ...[...documentUrls].map((url) => ({ kind: "document", url })),
  ...[...videoUrls].map((url) => ({ kind: "video", url })),
];

async function verify({ kind, url }) {
  const response = await fetch(url, { method: "HEAD", redirect: "follow" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  if (kind === "document") {
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.toLowerCase().includes("application/pdf")) {
      throw new Error(`unexpected content type ${contentType || "missing"}`);
    }
  }
}

let cursor = 0;
async function worker() {
  while (cursor < remoteChecks.length) {
    const item = remoteChecks[cursor++];
    try {
      await verify(item);
    } catch (error) {
      failures.push(`${item.kind}: ${item.url} (${error.message})`);
    }
  }
}

await Promise.all(Array.from({ length: concurrency }, () => worker()));

if (failures.length) {
  console.error("Council Intelligence source audit failed:");
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exitCode = 1;
} else {
  console.log(
    `Council Intelligence sources verified: ${documentUrls.size} PDFs, ` +
      `${videoUrls.size} video links, ${localImages.length} rendered pages.`,
  );
}
