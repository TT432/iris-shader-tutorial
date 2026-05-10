import fs from 'node:fs';
import path from 'node:path';

const dist = path.join(process.cwd(), 'dist');
const htmlFiles = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(fullPath);
    else if (entry.name.endsWith('.html')) htmlFiles.push(fullPath);
  }
}

walk(dist);

const rootAssetPattern = /(src|href)="\/(images|assets|_astro)\//;
const sparsePages = [];
const rootAssetPages = [];

for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf8');
  const rel = path.relative(dist, file).replaceAll(path.sep, '/');

  if (rootAssetPattern.test(html)) rootAssetPages.push(rel);
  if (rel !== '404.html') {
    const paragraphs = (html.match(/<p(\s|>)/g) || []).length;
    const codeBlocks = (html.match(/<pre(\s|>)/g) || []).length;
    const images = (html.match(/<img(\s|>)/g) || []).length;
    if (paragraphs < 3 && codeBlocks < 1 && images < 1) {
      sparsePages.push(`${rel} paragraphs=${paragraphs} pre=${codeBlocks} img=${images}`);
    }
  }
}

if (rootAssetPages.length) {
  console.error('Pages with root-relative asset paths:');
  for (const page of rootAssetPages) console.error(`- ${page}`);
}

if (sparsePages.length) {
  console.error('Pages with suspiciously sparse content:');
  for (const page of sparsePages) console.error(`- ${page}`);
}

if (rootAssetPages.length || sparsePages.length) process.exit(1);

console.log(`Validated ${htmlFiles.length} HTML files.`);
