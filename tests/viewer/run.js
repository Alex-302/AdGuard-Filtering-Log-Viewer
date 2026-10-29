const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const repoRoot = path.resolve(__dirname, "..", "..");
const viewerUrl = pathToFileURL(
  path.join(repoRoot, "filtering_log_viewer.html"),
).href;
const fixtureDir = path.resolve(__dirname, "..", "fixtures");
const fixture = (name) => path.join(fixtureDir, name);

const tests = [];
function test(name, fn) {
  tests.push({ name, fn });
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function load(page, fixtureName, width = 1600, height = 900) {
  await page.setViewportSize({ width, height });
  await page.goto(viewerUrl);
  await page.setInputFiles("#file-input", fixture(fixtureName));
  await page.waitForSelector("#virtual-rows tr.log-row");
  await page.waitForTimeout(250);
}

async function search(page, value) {
  await page.locator("#search").fill(value);
  await page.waitForTimeout(350);
  await page.waitForSelector("#virtual-rows tr.log-row");
}

async function enableSourceColumn(page) {
  await page.locator("#toggle-columns").click();
  await page.waitForTimeout(150);
  const input = page.locator('#columns-menu input[data-column="source"]');
  if (!(await input.isChecked())) await input.check();
  await page.waitForTimeout(200);
  await page.keyboard.press("Escape");
  await page.waitForTimeout(150);
}

function firstRow(page) {
  return page.locator("#virtual-rows tr.log-row").first();
}

function luminance(rgb) {
  const parts = rgb.match(/\d+/g).slice(0, 3).map(Number);
  const channels = parts.map((value) => {
    const channel = value / 255;
    return channel <= 0.03928
      ? channel / 12.92
      : Math.pow((channel + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrast(first, second) {
  const a = luminance(first);
  const b = luminance(second);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

test("new Android format and modules", async (page) => {
  await load(page, "android-new.json");
  assert.equal(await page.locator("#log-head th").count(), 7);
  assert.equal(await page.locator('#log-head th[data-col="app"]').count(), 1);
  assert.equal(await page.locator('#log-head th[data-col="process"]').count(), 0);

  await search(page, "stats.example.com");
  let row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="app"]').textContent(),
    "com.example.browser",
  );
  assert.match(
    await row.locator('td[data-col="type"]').textContent(),
    /Other, Ajax/,
  );
  assert.equal(
    await row.locator('td[data-col="filter"]').textContent(),
    "Tracking Protection",
  );
  assert.match(await row.locator('td[data-col="rule"]').textContent(), /^Stealth/);
  assert.equal(
    await row.locator(".rule-options-more").textContent(),
    "+2 Stealth",
  );
  assert.match(
    await row.locator(".rule-options-more").getAttribute("data-tooltip"),
    /Do Not Track/,
  );
  assert.match(
    await row.locator(".rule-options-more").getAttribute("data-tooltip"),
    /Remove X-Client-Data/,
  );
  assert.match(await row.getAttribute("class"), /category-modified/);
  await row.click();
  await wait(200);
  let details = await page.locator("#details").textContent();
  assert.match(details, /Web request/);
  assert.match(details, /Tracking Protection/);
  assert.match(details, /Do Not Track/);
  await page.keyboard.press("Escape");
  await wait(150);

  await search(page, "news.example.com");
  row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="filter"]').textContent(),
    "Tracking Protection",
  );
  assert.match(
    await row.locator('td[data-col="rule"]').textContent(),
    /^Cosmetic \/ Stealth/,
  );
  assert.equal(
    await row.locator(".rule-options-more").textContent(),
    "+3 Stealth",
  );
  assert.match(await row.getAttribute("class"), /category-cosmetic/);

  await search(page, "cosmetic-only");
  row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="filter"]').textContent(),
    "Cosmetic",
  );
  assert.match(await row.locator('td[data-col="rule"]').textContent(), /^Cosmetic/);
  assert.equal(await row.locator(".rule-options-more").textContent(), "+1");
  assert.doesNotMatch(
    await row.locator(".rule-options-more").textContent(),
    /Stealth/,
  );
  assert.match(await row.getAttribute("class"), /category-cosmetic/);
  await row.click();
  await wait(200);
  details = await page.locator("#details").textContent();
  assert.match(details, /Cosmetic rule/);
  await page.keyboard.press("Escape");
  await wait(150);

  await search(page, "challenges.example.com");
  row = firstRow(page);
  assert.equal(await row.locator('td[data-col="filter"]').textContent(), "");
  assert.equal(await row.locator('td[data-col="rule"]').textContent(), "—");
  assert.equal(await row.locator(".rule-options-more").count(), 0);
  assert.doesNotMatch(
    await row.locator('td[data-col="rule"]').textContent(),
    /Stealth/,
  );
  await row.click();
  await wait(200);
  details = await page.locator("#details").textContent();
  assert.match(details, /Modified Meta/);
  assert.doesNotMatch(details, /Permissions rule/);
  assert.match(details, /PERMISSIONS_RULE/);
  assert.equal(
    await page.locator("#details-rules .rule-option").count(),
    0,
  );
  await page.keyboard.press("Escape");
  await wait(150);

  await search(page, "ads.example.com");
  assert.ok(
    (await page.locator("#virtual-rows tr.category-blocked").count()) > 0,
    "Blocked rows are missing",
  );

  await search(page, "cdn.example.com");
  assert.ok(
    (await page.locator("#virtual-rows tr.category-allowed").count()) > 0,
    "Allowed rows are missing",
  );
});

test("domain lists, tooltips, and popups", async (page) => {
  await load(page, "android-new.json");
  await search(page, "cookieconsent");
  const ruleCell = firstRow(page).locator('td[data-col="rule"]');
  const ruleText = await ruleCell.textContent();
  assert.match(ruleText, /\.\.\.\+14\.\.\./);
  assert.equal(await ruleCell.locator(".rule-more").count(), 0);

  await ruleCell.hover();
  await wait(400);
  const popup = page.locator("#cell-tooltip");
  assert.equal(await popup.evaluate((el) => el.hidden), false);
  const popupText = await page.locator("#cell-tooltip-text").textContent();
  assert.match(popupText, /jagadzet\.pl/);
  const popupBox = await popup.boundingBox();
  const cellBox = await ruleCell.boundingBox();
  assert.ok(popupBox.width <= 1600 * 0.3 + 1, "Popup exceeds 30% width");
  assert.ok(
    popupBox.y >= cellBox.y + cellBox.height - 1,
    "Popup is not below the cell",
  );
  await page.mouse.move(popupBox.x + 10, popupBox.y + 10);
  await wait(300);
  assert.equal(
    await popup.evaluate((el) => el.hidden),
    false,
    "Popup closed while hovered",
  );
  await page.mouse.move(5, 5);
  await wait(400);
  assert.equal(await popup.evaluate((el) => el.hidden), true);

  await firstRow(page).click();
  await wait(200);
  const detailsRule = await page
    .locator("#details-rules .rule-row code")
    .first()
    .textContent();
  assert.match(detailsRule, /\.\.\.\+14\.\.\./);
  assert.equal(
    await page.locator("#details-rules .rule-row .rule-more").count(),
    0,
  );
  assert.equal(
    await page.locator("#details-rules .rule-row .copy-button").count(),
    1,
  );
  await page.keyboard.press("Escape");
  await wait(150);

  await search(page, "a.com,b.com");
  const cosmeticRule = await firstRow(page)
    .locator('td[data-col="rule"]')
    .textContent();
  assert.ok(
    cosmeticRule.includes(
      "a.com,b.com,c.com,...+14...r.com,s.com,t.com##.ad-banner",
    ),
    "Cosmetic domain list is not compacted",
  );

  await search(page, "stats.example.com");
  const typeHandle = page.locator(
    '#log-head th[data-col="type"] .col-resizer',
  );
  const typeBox = await typeHandle.boundingBox();
  await page.mouse.move(
    typeBox.x + typeBox.width / 2,
    typeBox.y + typeBox.height / 2,
  );
  await page.mouse.down();
  await page.mouse.move(
    typeBox.x + typeBox.width / 2 - 20,
    typeBox.y + typeBox.height / 2,
    { steps: 6 },
  );
  await page.mouse.up();
  await wait(200);
  await firstRow(page).locator('td[data-col="type"]').hover();
  await wait(400);
  assert.match(
    await page.locator("#cell-tooltip-text").textContent(),
    /Other, Ajax/,
  );
});

test("app lists are compacted", async (page) => {
  await page.addInitScript(() => {
    window.__copied = "";
    if (navigator.clipboard) {
      Object.defineProperty(navigator.clipboard, "writeText", {
        configurable: true,
        value: async (text) => {
          window.__copied = text;
        },
      });
    }
  });
  await load(page, "rule-app-lists.json");
  await search(page, "app-list.example");
  const ruleCell = firstRow(page).locator('td[data-col="rule"]');
  const ruleText = await ruleCell.textContent();
  assert.match(
    ruleText,
    /app=com\.example\.browser\|com\.example\.mail\|com\.example\.news\.\.\.\+14\.\.\.\|com\.discord\|com\.slack\|com\.microsoft\.teams$/,
  );
  assert.equal(await ruleCell.locator(".rule-more").count(), 0);
  const fullRule = await ruleCell.getAttribute("data-tooltip");
  assert.match(fullRule, /com\.microsoft\.teams$/);
  assert.doesNotMatch(fullRule, /\+14/);

  await ruleCell.hover();
  await wait(400);
  assert.equal(
    await page.locator("#cell-tooltip").evaluate((el) => el.hidden),
    false,
  );
  assert.equal(await page.locator("#cell-tooltip-text").textContent(), fullRule);
  await page.mouse.move(5, 5);
  await wait(400);

  await firstRow(page).click();
  await wait(200);
  const detailsCode = page.locator("#details-rules .rule-row code").first();
  assert.equal(await detailsCode.textContent(), ruleText);
  assert.equal(await detailsCode.getAttribute("title"), fullRule);
  assert.equal(
    await page.locator("#details-rules .rule-row .copy-button").count(),
    1,
  );
  await page.locator("#details-rules .rule-row .copy-button").first().click();
  await wait(150);
  assert.equal(await page.evaluate(() => window.__copied), fullRule);
  await page.keyboard.press("Escape");
  await wait(150);

  await search(page, "app-list-comma.example");
  const commaText = await firstRow(page)
    .locator('td[data-col="rule"]')
    .textContent();
  assert.match(
    commaText,
    /,app=com\.example\.browser\|com\.example\.mail\|com\.example\.news\.\.\.\+14\.\.\.\|com\.discord\|com\.slack\|com\.microsoft\.teams$/,
  );

  await search(page, "app-list-short.example");
  assert.equal(
    await firstRow(page).locator('td[data-col="rule"]').textContent(),
    "||app-list-short.example^$network,app=com.example.browser|com.example.mail|com.example.news",
  );

  await search(page, "app-list-dollar.example");
  const dollarText = await firstRow(page)
    .locator('td[data-col="rule"]')
    .textContent();
  assert.match(
    dollarText,
    /\$app=com\.example\.browser\|com\.example\.mail\|com\.example\.news\.\.\.\+14\.\.\.\|com\.discord\|com\.slack\|com\.microsoft\.teams$/,
  );

  await search(page, "app-list-both.example");
  const bothText = await firstRow(page)
    .locator('td[data-col="rule"]')
    .textContent();
  assert.match(
    bothText,
    /domain=site1\.com\|site2\.com\|site3\.com\.\.\.\+14\.\.\.\|site18\.com\|site19\.com\|site20\.com,app=com\.example\.browser\|com\.example\.mail\|com\.example\.news\.\.\.\+14\.\.\.\|com\.discord\|com\.slack\|com\.microsoft\.teams$/,
  );
});

test("tooltip stays open on click and uses larger fonts", async (page) => {
  await load(page, "type-long.json");
  const typeCell = firstRow(page).locator('td[data-col="type"]');
  await typeCell.hover();
  await wait(400);
  const popup = page.locator("#cell-tooltip");
  assert.equal(await popup.evaluate((el) => el.hidden), false);
  assert.equal(
    await popup.evaluate((el) => getComputedStyle(el).fontSize),
    "14px",
  );
  let box = await popup.boundingBox();
  await page.mouse.click(box.x + 20, box.y + 12);
  await wait(350);
  assert.equal(
    await popup.evaluate((el) => el.hidden),
    false,
    "Tooltip closed after a click on its text",
  );
  await page.mouse.move(5, 5);
  await wait(400);
  assert.equal(await popup.evaluate((el) => el.hidden), true);

  await load(page, "android-new.json");
  await search(page, "cookieconsent");
  const ruleCell = firstRow(page).locator('td[data-col="rule"]');
  await ruleCell.hover();
  await wait(400);
  assert.equal(await popup.evaluate((el) => el.hidden), false);
  assert.equal(
    await page
      .locator("#cell-tooltip-text")
      .evaluate((el) => getComputedStyle(el).fontSize),
    "13px",
  );
  assert.equal(
    await page
      .locator("#cell-tooltip-copy")
      .evaluate((el) => getComputedStyle(el).fontSize),
    "13px",
  );
  box = await popup.boundingBox();
  await page.mouse.click(box.x + 30, box.y + 12);
  await wait(350);
  assert.equal(
    await popup.evaluate((el) => el.hidden),
    false,
    "Mono tooltip closed after a click on its text",
  );
  await page.mouse.move(5, 5);
  await wait(400);
  assert.equal(await popup.evaluate((el) => el.hidden), true);
});

test("empty Source and Filter cells stay blank", async (page) => {
  await load(page, "empty-source-filter.json");
  await enableSourceColumn(page);
  assert.equal(await page.locator('#log-head th[data-col="source"]').count(), 1);

  for (const term of [
    "dns://ads.example.com",
    "203.0.113.10",
    "tunnel.example.com",
    "1.2.3.4",
  ]) {
    await search(page, term);
    const row = firstRow(page);
    assert.equal(
      await row.locator('td[data-col="source"]').textContent(),
      "",
      `Source is not blank for ${term}`,
    );
    assert.equal(
      await row.locator('td[data-col="filter"]').textContent(),
      "",
      `Filter is not blank for ${term}`,
    );
  }

  await search(page, "ads.example.com/banner.js");
  assert.equal(
    await firstRow(page).locator('td[data-col="filter"]').textContent(),
    "AdGuard Base filter",
  );

  await load(page, "android-connections.json");
  await enableSourceColumn(page);
  await search(page, "tcp://example.com");
  assert.equal(
    await firstRow(page).locator('td[data-col="source"]').textContent(),
    "",
  );
  assert.equal(
    await firstRow(page).locator('td[data-col="filter"]').textContent(),
    "",
  );
  await search(page, "203.0.113.10");
  assert.equal(
    await firstRow(page).locator('td[data-col="source"]').textContent(),
    "",
  );
  assert.equal(
    await firstRow(page).locator('td[data-col="filter"]').textContent(),
    "",
  );

  await load(page, "android-new.json");
  await enableSourceColumn(page);
  await search(page, "dns://ads.example.com");
  assert.equal(
    await firstRow(page).locator('td[data-col="source"]').textContent(),
    "",
  );
  assert.equal(
    await firstRow(page).locator('td[data-col="filter"]').textContent(),
    "DNS filter 2",
  );

  await load(page, "android-old.json");
  await enableSourceColumn(page);
  await search(page, "1.2.3.4");
  assert.equal(
    await firstRow(page).locator('td[data-col="source"]').textContent(),
    "",
  );
  assert.equal(
    await firstRow(page).locator('td[data-col="filter"]').textContent(),
    "User Rules",
  );
});

test("firewall strategy mapping", async (page) => {
  await load(page, "firewall-strategy.json");
  const row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="rule"]').textContent(),
    "blockedByAppRuleOnWifi (WiFi)",
  );
  assert.equal(await row.locator('td[data-col="filter"]').textContent(), "");
  assert.equal(
    await row.locator('td[data-col="rule"]').getAttribute("data-tooltip"),
    "blockedByAppRuleOnWifi (WiFi)",
  );
  await row.click();
  await wait(200);
  const firewall = await page.evaluate(() => {
    const term = [...document.querySelectorAll("#details-fields dt")].find(
      (element) => element.textContent === "Firewall",
    );
    return term && term.nextElementSibling
      ? term.nextElementSibling.textContent
      : "";
  });
  assert.equal(firewall.trim(), "blockedByAppRuleOnWifi (WiFi)");
  assert.doesNotMatch(
    await page.locator("#details-fields").textContent(),
    /Blocked By App Rule On Wifi/,
  );
});

test("Type column resize cap", async (page) => {
  await load(page, "type-long.json");
  const typeCell = firstRow(page).locator('td[data-col="type"]');
  assert.match(await typeCell.textContent(), /HTML/);
  assert.match(await typeCell.textContent(), /Subdocument/);

  const handle = page.locator('#log-head th[data-col="type"] .col-resizer');
  let box = await handle.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(
    box.x + box.width / 2 + 200,
    box.y + box.height / 2,
    { steps: 10 },
  );
  await page.mouse.up();
  await wait(250);
  let width = await page
    .locator('#log-cols col[data-col="type"]')
    .evaluate((el) => parseFloat(el.style.width));
  assert.ok(width > 200, `Type column width is ${width}`);
  assert.ok(
    await typeCell.evaluate((el) => {
      const text = el.querySelector(".cell-type-text");
      return text.scrollWidth <= text.clientWidth + 1;
    }),
    "Type text is still truncated",
  );
  await typeCell.hover();
  await wait(400);
  assert.equal(
    await page.locator("#cell-tooltip").evaluate((el) => el.hidden),
    true,
    "Tooltip appeared for fitting Type text",
  );

  await handle.focus();
  for (let index = 0; index < 20; index += 1) {
    await page.keyboard.press("ArrowRight");
  }
  await wait(250);
  width = await page
    .locator('#log-cols col[data-col="type"]')
    .evaluate((el) => parseFloat(el.style.width));
  assert.equal(width, 480);

  await page.setViewportSize({ width: 1000, height: 800 });
  await wait(400);
  assert.equal(await page.locator("#log-table").evaluate((el) => el.hidden), false);
  width = await page
    .locator('#log-cols col[data-col="type"]')
    .evaluate((el) => parseFloat(el.style.width));
  assert.ok(width > 200, `Narrow Type column width is ${width}`);
});

test("sorting, resizing, and column visibility", async (page) => {
  await load(page, "android-new.json");
  const urlHeader = page.locator('#log-head th[data-col="url"]');
  await urlHeader.click({ position: { x: 3, y: 3 } });
  await wait(200);
  assert.equal(await urlHeader.getAttribute("aria-sort"), "ascending");
  await urlHeader.click({ position: { x: 3, y: 3 } });
  await wait(200);
  assert.equal(await urlHeader.getAttribute("aria-sort"), "descending");

  const handle = page.locator('#log-head th[data-col="url"] .col-resizer');
  assert.match(await handle.getAttribute("title"), /Double-click/);
  const before = await page
    .locator('#log-cols col[data-col="url"]')
    .evaluate((el) => parseFloat(el.style.width));
  const box = await handle.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(
    box.x + box.width / 2 + 50,
    box.y + box.height / 2,
    { steps: 8 },
  );
  await page.mouse.up();
  await wait(200);
  const after = await page
    .locator('#log-cols col[data-col="url"]')
    .evaluate((el) => parseFloat(el.style.width));
  assert.ok(after > before + 20, "Resize did not change the URL width");
  await handle.dblclick();
  await wait(250);
  const reset = await page
    .locator('#log-cols col[data-col="url"]')
    .evaluate((el) => parseFloat(el.style.width));
  assert.ok(reset < after - 20, "Double-click did not reset the column");

  await page.locator('#log-head th[data-col="app"]').click({
    button: "right",
  });
  await wait(200);
  assert.equal(
    await page.locator("#columns-menu").evaluate((el) => el.hidden),
    false,
  );
  const options = await page
    .locator("#columns-menu input[data-column]")
    .evaluateAll((els) => els.map((el) => el.dataset.column));
  assert.deepEqual(options, [
    "app",
    "type",
    "rule",
    "method",
    "filter",
    "source",
  ]);
  assert.ok(!options.includes("time") && !options.includes("url"));
  await page.locator('#columns-menu input[data-column="app"]').uncheck();
  await wait(200);
  assert.equal(
    await page.locator('#log-head th[data-col="app"]').count(),
    0,
  );
  await page.locator("#reset-columns").click();
  await wait(200);
  assert.equal(
    await page.locator('#log-head th[data-col="app"]').count(),
    1,
  );
  await page.keyboard.press("Escape");
});

test("Ctrl-F and slash shortcuts", async (page) => {
  await load(page, "android-new.json");
  await firstRow(page).click();
  await wait(200);
  await page.keyboard.press("Control+f");
  await wait(150);
  assert.equal(
    await page.evaluate(() => document.activeElement && document.activeElement.id),
    "search",
  );

  await page.locator("#toggle-columns").click();
  await wait(150);
  assert.equal(
    await page.locator("#columns-menu").evaluate((el) => el.hidden),
    false,
  );
  await page.keyboard.press("/");
  await wait(150);
  assert.equal(
    await page.locator("#columns-menu").evaluate((el) => el.hidden),
    true,
  );
  assert.equal(
    await page.evaluate(() => document.activeElement && document.activeElement.id),
    "search",
  );

  await page.setViewportSize({ width: 800, height: 800 });
  await wait(250);
  await page.locator("#toggle-filters").click();
  await wait(200);
  assert.equal(
    await page
      .locator(".app-shell")
      .evaluate((el) => el.classList.contains("sidebar-open")),
    true,
  );
  await page.keyboard.press("/");
  await wait(200);
  assert.equal(
    await page
      .locator(".app-shell")
      .evaluate((el) => el.classList.contains("sidebar-open")),
    false,
  );
  assert.equal(
    await page.evaluate(() => document.activeElement && document.activeElement.id),
    "search",
  );

  await page.setViewportSize({ width: 700, height: 800 });
  await wait(250);
  await firstRow(page).click();
  await wait(200);
  assert.equal(
    await page.locator("#details").evaluate((el) => el.hidden),
    false,
  );
  await page.keyboard.press("/");
  await wait(200);
  assert.equal(
    await page.locator("#details").evaluate((el) => el.hidden),
    true,
  );
  assert.equal(
    await page.evaluate(() => document.activeElement && document.activeElement.id),
    "search",
  );
});

test("hide list draft, Save, and Reset", async (page) => {
  await load(page, "android-new.json");
  await page.locator("#open-hide-list").click();
  await wait(200);
  assert.equal(await page.locator("#done-hide").isDisabled(), true);
  assert.equal(
    await page.locator("#hide-draft-state").textContent(),
    "Saved",
  );

  await page.locator("#domain-input").fill("example.com");
  await page.locator("#add-domain").click();
  await wait(150);
  assert.equal(await page.locator("#done-hide").isDisabled(), false);
  await page.locator("#close-hide").click();
  await wait(250);
  await page.locator("#open-hide-list").click();
  await wait(200);
  assert.equal(await page.locator("#done-hide").isDisabled(), true);
  assert.equal(await page.locator("#domain-list .hide-row").count(), 0);

  await page.locator("#hide-file-input").setInputFiles(
    fixture("hide-list.agfilters"),
  );
  await wait(400);
  assert.equal(await page.locator("#done-hide").isDisabled(), false);
  assert.equal(await page.locator("#domain-list .hide-row").count(), 2);
  await page.locator("#close-hide").click();
  await wait(250);
  await page.locator("#open-hide-list").click();
  await wait(200);
  assert.equal(await page.locator("#domain-list .hide-row").count(), 0);

  await page.locator("#hide-file-input").setInputFiles(
    fixture("hide-list.agfilters"),
  );
  await wait(400);
  await page.locator("#done-hide").click();
  await wait(300);
  assert.equal(
    await page.locator("#hide-modal").evaluate((el) => el.hidden),
    true,
  );
  await page.locator("#open-hide-list").click();
  await wait(200);
  assert.equal(await page.locator("#done-hide").isDisabled(), true);
  assert.equal(await page.locator("#domain-list .hide-row").count(), 2);
  assert.equal(await page.locator("#hide-enabled-modal").isChecked(), true);

  page.once("dialog", (dialog) => dialog.accept());
  await page.locator("#clear-hide").click();
  await wait(250);
  assert.equal(
    await page.locator("#hide-enabled-modal").isChecked(),
    false,
  );
  assert.equal(await page.locator("#done-hide").isDisabled(), false);
  await page.locator("#close-hide").click();
  await wait(250);
  await page.locator("#open-hide-list").click();
  await wait(200);
  assert.equal(await page.locator("#domain-list .hide-row").count(), 2);
  assert.equal(await page.locator("#hide-enabled-modal").isChecked(), true);
  assert.equal(await page.locator("#done-hide").isDisabled(), true);
  await page.locator("#close-hide").click();
});

test("responsive details", async (page) => {
  await load(page, "android-new.json", 1000, 800);
  await firstRow(page).click();
  await wait(200);
  assert.equal(
    await page.locator("#details").evaluate((el) => getComputedStyle(el).position),
    "static",
  );
  assert.equal(await page.locator("#details-backdrop").count(), 0);
  assert.equal(
    await page.locator(".content").evaluate((el) => el.inert),
    false,
  );
  const first = await page.locator("#details-domain").textContent();
  await page.locator("#virtual-rows tr.log-row").nth(2).click();
  await wait(200);
  const second = await page.locator("#details-domain").textContent();
  assert.notEqual(first, second, "Tablet row click did not update details");
  await page.keyboard.press("Escape");
  await wait(150);

  await page.setViewportSize({ width: 700, height: 800 });
  await wait(250);
  await firstRow(page).click();
  await wait(200);
  assert.equal(
    await page.locator("#details").evaluate((el) => getComputedStyle(el).position),
    "fixed",
  );
  assert.equal(
    await page.locator("#details").evaluate((el) => el.getBoundingClientRect().width),
    700,
  );
  assert.equal(await page.locator("#details").getAttribute("role"), "dialog");
  assert.equal(
    await page.locator(".content").evaluate((el) => el.inert),
    true,
  );
  await page.keyboard.press("Escape");
  await wait(150);

  await page.setViewportSize({ width: 1440, height: 900 });
  await wait(250);
  await firstRow(page).click();
  await wait(200);
  assert.notEqual(
    await page
      .locator("#details-resizer")
      .evaluate((el) => getComputedStyle(el).display),
    "none",
  );
  await page.keyboard.press("Escape");
});

test("row colors and contrast", async (page) => {
  await load(page, "android-new.json");
  const values = await page.evaluate(() => {
    const result = {};
    for (const name of ["blocked", "allowed", "modified", "cosmetic"]) {
      const chip = document.querySelector(`.chip.${name}`);
      const row = document.querySelector(
        `#virtual-rows tr.category-${name} td`,
      );
      result[name] = [
        chip && getComputedStyle(chip).backgroundColor,
        row && getComputedStyle(row).backgroundColor,
      ];
    }
    return result;
  });
  for (const [name, [chip, row]] of Object.entries(values)) {
    assert.equal(row, chip, `${name} row color does not match the legend`);
  }

  await search(page, "ads.example.com");
  const colors = await page.evaluate(() => {
    const row = document.querySelector("#virtual-rows tr.category-blocked");
    const text = row.querySelector(".cell-type-text");
    return {
      background: getComputedStyle(row.querySelector("td")).backgroundColor,
      text: getComputedStyle(text).color,
    };
  });
  assert.ok(
    contrast(colors.background, colors.text) >= 4.5,
    "Secondary row text is below 4.5:1",
  );
});

test("old Android format", async (page) => {
  await load(page, "android-old.json");
  await search(page, "example.com/page");
  let row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="type"]').textContent(),
    "HTML",
  );
  assert.match(await row.getAttribute("class"), /category-processed/);

  await search(page, "banner.js");
  row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="type"]').textContent(),
    "Script",
  );
  assert.match(await row.getAttribute("class"), /category-blocked/);

  await search(page, "dns://ads.example.com");
  row = firstRow(page);
  assert.equal(await row.locator('td[data-col="type"]').textContent(), "DNS");
  assert.match(await row.getAttribute("class"), /category-blocked/);

  await search(page, "1.2.3.4");
  row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="type"]').textContent(),
    "Whitelist",
  );
  assert.match(await row.getAttribute("class"), /category-allowed/);
});

test("connections-only Android format", async (page) => {
  await load(page, "android-connections.json");
  await search(page, "tcp://example.com");
  let row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="type"]').textContent(),
    "Connection",
  );

  await search(page, "tcp://ads.example.com");
  row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="type"]').textContent(),
    "Connection",
  );
  assert.match(await row.getAttribute("class"), /category-blocked/);

  await search(page, "203.0.113.10");
  row = firstRow(page);
  assert.equal(
    await row.locator('td[data-col="type"]').textContent(),
    "Firewall",
  );
  const types = await page
    .locator('#virtual-rows tr.log-row td[data-col="type"]')
    .allTextContents();
  assert.ok(!types.includes("Other"));
});

test("appPath in App column and details", async (page) => {
  await load(page, "app-path.json");
  assert.equal(
    await firstRow(page).locator('td[data-col="app"]').textContent(),
    "chrome.exe",
  );
  await firstRow(page).click();
  await wait(200);
  assert.match(await page.locator("#details").textContent(), /chrome\.exe/);
  await page.keyboard.press("Escape");
});

test("opening details keeps the sort order and scroll position", async (page) => {
  await load(page, "long-list.json");
  await page.locator('#log-head th[data-col="app"]').click({
    position: { x: 3, y: 3 },
  });
  await wait(300);
  await page.evaluate(() => {
    document.querySelector("#record-list").scrollTop = 150 * 32;
  });
  await wait(300);
  const before = await page.evaluate(() => {
    const list = document.querySelector("#record-list");
    const head = document.querySelector("#log-head");
    const top = list.getBoundingClientRect().top + head.offsetHeight;
    const row = [...document.querySelectorAll("#virtual-rows tr.log-row")].find(
      (item) => item.getBoundingClientRect().top > top + 40,
    );
    return {
      scrollTop: list.scrollTop,
      index: row.dataset.index,
      url: row.querySelector('td[data-col="url"]').textContent,
    };
  });
  await page
    .locator(`#virtual-rows tr.log-row[data-index="${before.index}"]`)
    .click();
  await wait(500);
  const after = await page.evaluate(() => {
    const list = document.querySelector("#record-list");
    const row = document.querySelector("#virtual-rows tr.log-row.selected");
    return {
      scrollTop: list.scrollTop,
      index: row ? row.dataset.index : null,
      url: row ? row.querySelector('td[data-col="url"]').textContent : null,
      detailsOpen: !document.querySelector("#details").hidden,
    };
  });
  assert.equal(after.detailsOpen, true);
  assert.equal(after.url, before.url, "Selected record changed");
  assert.ok(
    Math.abs(after.scrollTop - before.scrollTop) <= 1,
    `List jumped from ${before.scrollTop} to ${after.scrollTop}`,
  );

  await page.keyboard.press("Escape");
  await wait(300);
  assert.equal(
    await page.locator('#log-head th[data-col="app"]').getAttribute("aria-sort"),
    "ascending",
  );
  const afterClose = await page
    .locator("#record-list")
    .evaluate((el) => el.scrollTop);
  assert.ok(
    Math.abs(afterClose - before.scrollTop) <= 1,
    "List jumped after details closed",
  );
});

test("settings export shows a clear import error", async (page) => {
  await page.goto(viewerUrl);
  await page.setInputFiles("#file-input", fixture("settings-export.json"));
  await wait(300);
  assert.equal(
    await page.locator("#error").evaluate((el) => el.hidden),
    false,
  );
  const error = await page.locator("#error-text").textContent();
  assert.match(error, /settings export/i);
  assert.match(error, /recent_activity\.json/i);
});

async function main() {
  const browser = await chromium.launch();
  let failed = 0;

  for (const { name, fn } of tests) {
    const context = await browser.newContext({
      viewport: { width: 1600, height: 900 },
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });

    try {
      await fn(page);
      assert.deepEqual(errors, [], `Page errors:\n${errors.join("\n")}`);
      console.log(`ok - ${name}`);
    } catch (error) {
      failed += 1;
      console.error(`FAIL - ${name}`);
      console.error(error.stack || error);
    } finally {
      await context.close();
    }
  }

  await browser.close();
  if (failed) {
    console.error(`\n${failed} viewer test(s) failed.`);
    process.exit(1);
  }
  console.log(`\n${tests.length} viewer tests passed.`);
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
