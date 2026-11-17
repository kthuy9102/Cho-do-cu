const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const assert = require("node:assert/strict");

const frontendDir = path.resolve(__dirname, "..");

test("all local HTML script and stylesheet references exist", () => {
  const htmlFiles = fs.readdirSync(frontendDir).filter((name) => name.endsWith(".html"));
  assert.ok(htmlFiles.length > 0, "No frontend HTML pages were found");

  for (const htmlFile of htmlFiles) {
    const html = fs.readFileSync(path.join(frontendDir, htmlFile), "utf8");
    const references = [...html.matchAll(/(?:src|href)\s*=\s*["']([^"']+)["']/gi)];

    for (const [, reference] of references) {
      if (/^(?:[a-z]+:|\/\/|#)/i.test(reference)) continue;

      const localPath = reference.split(/[?#]/, 1)[0];
      if (!localPath) continue;

      const target = path.resolve(frontendDir, path.dirname(htmlFile), localPath);
      assert.ok(
        fs.existsSync(target),
        `${htmlFile} references missing local asset: ${reference}`,
      );
    }
  }
});

test("frontend API clients use the same-origin versioned API behind Nginx", () => {
  const api = fs.readFileSync(path.join(frontendDir, "api.js"), "utf8");
  const auth = fs.readFileSync(path.join(frontendDir, "auth.js"), "utf8");

  assert.match(api, /["']\/api\/v1["']/);
  assert.match(auth, /AUTH_API\s*=\s*["']\/api\/v1["']/);
});
