import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";

const root = resolve("dist");

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? walk(path) : [path];
  });
}

function outputUrl(path) {
  const directory = relative(root, dirname(path)).split(sep).join("/");
  return directory ? `/${directory}` : "/";
}

function targetExists(url) {
  const pathname = decodeURIComponent(url.pathname);
  if (pathname === "/") return existsSync(join(root, "index.html"));
  const relativePath = pathname.replace(/^\//, "");
  return (
    existsSync(join(root, relativePath)) ||
    existsSync(join(root, relativePath, "index.html"))
  );
}

const files = walk(root);
const pages = files.filter((path) => path.endsWith("index.html"));
const emittedPages = new Set(pages.map(outputUrl));
const problems = [];

for (const path of pages) {
  const html = readFileSync(path, "utf8");
  const pageUrl = outputUrl(path);
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1]);
  const duplicates = [
    ...new Set(ids.filter((id, index) => ids.indexOf(id) !== index)),
  ];
  if (duplicates.length)
    problems.push(`${pageUrl}: duplicate ids ${duplicates.join(", ")}`);

  for (const match of html.matchAll(
    /<(?:a|link|script|img)\b[^>]+(?:href|src)="([^"]+)"/g,
  )) {
    const value = match[1];
    if (value.startsWith("#") || value.startsWith("mailto:")) continue;
    const url = new URL(value, "https://careero.app");
    if (url.origin === "https://careero.app" && !targetExists(url)) {
      problems.push(`${pageUrl}: missing target ${url.pathname}`);
    }
  }

  for (const match of html.matchAll(
    /<script type="application\/ld\+json">(.*?)<\/script>/gs,
  )) {
    let data;
    try {
      data = JSON.parse(match[1]);
    } catch (error) {
      problems.push(`${pageUrl}: invalid JSON-LD (${error.message})`);
      continue;
    }
    if (data["@type"] === "BreadcrumbList") {
      for (const item of data.itemListElement) {
        const pathname = new URL(item.item).pathname.replace(/\/$/, "") || "/";
        if (!emittedPages.has(pathname)) {
          problems.push(
            `${pageUrl}: breadcrumb target not emitted ${pathname}`,
          );
        }
      }
    }
    if (data["@type"] === "Article") {
      const image = new URL(data.image);
      if (!targetExists(image))
        problems.push(`${pageUrl}: article image missing ${image.pathname}`);
    }
  }
}

if (problems.length) {
  console.error(problems.join("\n"));
  process.exit(1);
}

console.log(`Validated ${pages.length} generated pages.`);
