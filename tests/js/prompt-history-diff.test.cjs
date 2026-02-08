const test = require("node:test");
const assert = require("node:assert/strict");

const { buildPromptHistoryDiffRows } = require("../../static/js/prompt-history-diff.js");

function getLineRows(rows) {
    return rows.filter(row => row.type === "line");
}

test("categories diff uses user-facing lines and side-by-side change rows", () => {
    const previous = {
        categories: [{ name: "Technology", definition: "Tech updates" }],
    };
    const current = {
        categories: [{ name: "Technology", definition: "Global tech updates" }],
    };

    const rows = buildPromptHistoryDiffRows("categories", current, previous);
    const lineRows = getLineRows(rows);

    assert.ok(rows.some(row => row.type === "hunk-header" && row.text.includes("@@")));
    assert.ok(
        lineRows.some(row => (
            row.left &&
            row.right &&
            row.left.kind === "removed" &&
            row.right.kind === "added" &&
            row.left.text.includes("Definition: Tech updates") &&
            row.right.text.includes("Definition: Global tech updates")
        )),
    );
    assert.ok(lineRows.every(row => (!row.left || !row.left.text.includes("{"))));
    assert.ok(lineRows.every(row => (!row.right || !row.right.text.includes("{"))));
    assert.ok(lineRows.every(row => (!row.left || !row.left.text.includes("\"categories\""))));
});

test("system prompt first version renders only right-side additions", () => {
    const current = {
        content: "Line one\nLine two",
    };

    const rows = buildPromptHistoryDiffRows("systemprompt", current, null);
    const lineRows = getLineRows(rows);

    assert.ok(rows.some(row => row.type === "hunk-header" && row.text.includes("-0,0")));
    assert.ok(lineRows.every(row => row.left === null));
    assert.ok(lineRows.every(row => row.right && row.right.kind === "added"));
});

test("few-shots diff hides JSON structure and preserves field labels", () => {
    const previous = {
        examples: [{
            id: "ex-001",
            news_content: "Old news",
            category: "Tech",
            reasoning: "Old reason",
        }],
    };
    const current = {
        examples: [{
            id: "ex-001",
            news_content: "New news",
            category: "Tech",
            reasoning: "Old reason",
        }],
    };

    const rows = buildPromptHistoryDiffRows("fewshots", current, previous);
    const lineRows = getLineRows(rows);

    assert.ok(
        lineRows.some(row => (
            row.left &&
            row.left.text.includes("News Content: Old news")
        )),
    );
    assert.ok(
        lineRows.some(row => (
            row.right &&
            row.right.text.includes("News Content: New news")
        )),
    );
    assert.ok(lineRows.every(row => (!row.left || !row.left.text.includes("\"news_content\""))));
});

test("buildPromptHistoryDiffRows returns info row when versions are identical", () => {
    const content = {
        examples: [{ id: "ex-001", news_content: "News", category: "Tech", reasoning: "Reason" }],
    };

    const rows = buildPromptHistoryDiffRows("fewshots", content, content);

    assert.equal(rows.length, 1);
    assert.equal(rows[0].type, "info");
    assert.equal(rows[0].text, "No content changes between versions.");
});
