(function (globalScope) {
    "use strict";

    const DIFF_CONTEXT_LINES = 3;

    function requireValue(name, value) {
        if (value === undefined) {
            throw new Error(`${name} is required`);
        }
        return value;
    }

    function requireString(name, value) {
        requireValue(name, value);
        if (typeof value !== "string") {
            throw new Error(`${name} must be a string`);
        }
        return value;
    }

    function appendLabeledText(lines, label, value) {
        requireValue("lines", lines);
        requireString("label", label);
        const text = requireString(label, value);
        const valueLines = text.split("\n");
        lines.push(`${label}: ${valueLines[0]}`);
        for (let i = 1; i < valueLines.length; i += 1) {
            lines.push(`  ${valueLines[i]}`);
        }
    }

    function validateCategory(category, index) {
        requireValue(`categories[${index}]`, category);
        requireString(`categories[${index}].name`, category.name);
        requireString(`categories[${index}].definition`, category.definition);
    }

    function formatCategoriesContent(content) {
        requireValue("content.categories", content.categories);
        if (!Array.isArray(content.categories)) {
            throw new Error("content.categories must be an array");
        }
        const lines = [];
        content.categories.forEach((category, index) => {
            validateCategory(category, index);
            lines.push(`Category ${index + 1}: ${category.name}`);
            appendLabeledText(lines, "Definition", category.definition);
            if (index < content.categories.length - 1) {
                lines.push("");
            }
        });
        return lines;
    }

    function validateExample(example, index) {
        requireValue(`examples[${index}]`, example);
        requireString(`examples[${index}].id`, example.id);
        requireString(`examples[${index}].news_content`, example.news_content);
        requireString(`examples[${index}].category`, example.category);
        requireString(`examples[${index}].reasoning`, example.reasoning);
    }

    function formatFewShotsContent(content) {
        requireValue("content.examples", content.examples);
        if (!Array.isArray(content.examples)) {
            throw new Error("content.examples must be an array");
        }
        const lines = [];
        content.examples.forEach((example, index) => {
            validateExample(example, index);
            lines.push(`Example ${index + 1}`);
            appendLabeledText(lines, "ID", example.id);
            appendLabeledText(lines, "News Content", example.news_content);
            appendLabeledText(lines, "Category", example.category);
            appendLabeledText(lines, "Reasoning", example.reasoning);
            if (index < content.examples.length - 1) {
                lines.push("");
            }
        });
        return lines;
    }

    function formatSystemPromptContent(content) {
        const promptText = requireString("content.content", content.content);
        return promptText.split("\n");
    }

    function formatPromptContentLines(type, content) {
        requireString("type", type);
        requireValue("content", content);
        if (type === "categories") {
            return formatCategoriesContent(content);
        }
        if (type === "fewshots") {
            return formatFewShotsContent(content);
        }
        if (type === "systemprompt") {
            return formatSystemPromptContent(content);
        }
        throw new Error(`Unknown prompt history type: ${type}`);
    }

    function buildLcsMatrix(previousLines, currentLines) {
        requireValue("previousLines", previousLines);
        requireValue("currentLines", currentLines);

        const matrix = Array.from({ length: previousLines.length + 1 }, () => (
            Array(currentLines.length + 1).fill(0)
        ));

        for (let i = previousLines.length - 1; i >= 0; i -= 1) {
            for (let j = currentLines.length - 1; j >= 0; j -= 1) {
                if (previousLines[i] === currentLines[j]) {
                    matrix[i][j] = matrix[i + 1][j + 1] + 1;
                    continue;
                }
                matrix[i][j] = Math.max(matrix[i + 1][j], matrix[i][j + 1]);
            }
        }
        return matrix;
    }

    function buildDiffOperations(previousLines, currentLines) {
        requireValue("previousLines", previousLines);
        requireValue("currentLines", currentLines);

        const matrix = buildLcsMatrix(previousLines, currentLines);
        const operations = [];
        let i = 0;
        let j = 0;
        let oldLineNumber = 1;
        let newLineNumber = 1;

        while (i < previousLines.length && j < currentLines.length) {
            if (previousLines[i] === currentLines[j]) {
                operations.push({
                    type: "context",
                    text: previousLines[i],
                    oldLineNumber,
                    newLineNumber,
                });
                i += 1;
                j += 1;
                oldLineNumber += 1;
                newLineNumber += 1;
                continue;
            }

            if (matrix[i + 1][j] >= matrix[i][j + 1]) {
                operations.push({
                    type: "removed",
                    text: previousLines[i],
                    oldLineNumber,
                    newLineNumber: null,
                });
                i += 1;
                oldLineNumber += 1;
                continue;
            }

            operations.push({
                type: "added",
                text: currentLines[j],
                oldLineNumber: null,
                newLineNumber,
            });
            j += 1;
            newLineNumber += 1;
        }

        while (i < previousLines.length) {
            operations.push({
                type: "removed",
                text: previousLines[i],
                oldLineNumber,
                newLineNumber: null,
            });
            i += 1;
            oldLineNumber += 1;
        }

        while (j < currentLines.length) {
            operations.push({
                type: "added",
                text: currentLines[j],
                oldLineNumber: null,
                newLineNumber,
            });
            j += 1;
            newLineNumber += 1;
        }

        return operations;
    }

    function findChangedRanges(operations) {
        requireValue("operations", operations);

        const changedIndices = operations
            .map((row, index) => ({ row, index }))
            .filter(item => item.row.type !== "context")
            .map(item => item.index);
        if (changedIndices.length === 0) {
            return [];
        }

        const ranges = [];
        let currentStart = null;
        let currentEnd = null;

        changedIndices.forEach(index => {
            const nextStart = Math.max(0, index - DIFF_CONTEXT_LINES);
            const nextEnd = Math.min(operations.length - 1, index + DIFF_CONTEXT_LINES);
            if (currentStart === null) {
                currentStart = nextStart;
                currentEnd = nextEnd;
                return;
            }
            if (nextStart <= currentEnd + 1) {
                currentEnd = Math.max(currentEnd, nextEnd);
                return;
            }
            ranges.push({ start: currentStart, end: currentEnd });
            currentStart = nextStart;
            currentEnd = nextEnd;
        });

        ranges.push({ start: currentStart, end: currentEnd });
        return ranges;
    }

    function getLineRangeDetails(hunkRows, lineNumberKey) {
        requireValue("hunkRows", hunkRows);
        requireValue("lineNumberKey", lineNumberKey);

        const lineNumbers = hunkRows
            .filter(row => row[lineNumberKey] !== null)
            .map(row => row[lineNumberKey]);

        if (lineNumbers.length === 0) {
            return { start: 0, count: 0 };
        }
        return {
            start: lineNumbers[0],
            count: lineNumbers.length,
        };
    }

    function buildHunkHeader(hunkRows) {
        requireValue("hunkRows", hunkRows);
        const oldRange = getLineRangeDetails(hunkRows, "oldLineNumber");
        const newRange = getLineRangeDetails(hunkRows, "newLineNumber");
        return `@@ -${oldRange.start},${oldRange.count} +${newRange.start},${newRange.count} @@`;
    }

    function buildLeftSide(operation) {
        if (operation === null) {
            return null;
        }
        if (operation.type === "context") {
            return {
                lineNumber: operation.oldLineNumber,
                text: operation.text,
                kind: "context",
            };
        }
        if (operation.type === "removed") {
            return {
                lineNumber: operation.oldLineNumber,
                text: operation.text,
                kind: "removed",
            };
        }
        throw new Error("Left side supports only context or removed operations");
    }

    function buildRightSide(operation) {
        if (operation === null) {
            return null;
        }
        if (operation.type === "context") {
            return {
                lineNumber: operation.newLineNumber,
                text: operation.text,
                kind: "context",
            };
        }
        if (operation.type === "added") {
            return {
                lineNumber: operation.newLineNumber,
                text: operation.text,
                kind: "added",
            };
        }
        throw new Error("Right side supports only context or added operations");
    }

    function buildSideBySideLineRow(leftOperation, rightOperation) {
        return {
            type: "line",
            left: buildLeftSide(leftOperation),
            right: buildRightSide(rightOperation),
        };
    }

    function pairChangedOperations(changedOperations) {
        requireValue("changedOperations", changedOperations);
        const removed = changedOperations.filter(operation => operation.type === "removed");
        const added = changedOperations.filter(operation => operation.type === "added");
        const total = Math.max(removed.length, added.length);

        const rows = [];
        for (let i = 0; i < total; i += 1) {
            rows.push(buildSideBySideLineRow(removed[i] || null, added[i] || null));
        }
        return rows;
    }

    function buildSideBySideRowsForOperations(operations) {
        requireValue("operations", operations);
        const rows = [];
        let index = 0;
        while (index < operations.length) {
            const operation = operations[index];
            if (operation.type === "context") {
                rows.push(buildSideBySideLineRow(operation, operation));
                index += 1;
                continue;
            }

            const changedBlock = [];
            while (index < operations.length && operations[index].type !== "context") {
                changedBlock.push(operations[index]);
                index += 1;
            }
            rows.push(...pairChangedOperations(changedBlock));
        }
        return rows;
    }

    function buildInitialSideBySideRows(currentLines) {
        requireValue("currentLines", currentLines);
        const rows = [{
            type: "hunk-header",
            text: `@@ -0,0 +1,${currentLines.length} @@`,
        }];

        currentLines.forEach((line, lineIndex) => {
            rows.push(buildSideBySideLineRow(null, {
                type: "added",
                text: line,
                oldLineNumber: null,
                newLineNumber: lineIndex + 1,
            }));
        });
        return rows;
    }

    function buildPromptHistoryDiffRows(type, currentContent, previousContent) {
        requireString("type", type);
        requireValue("currentContent", currentContent);
        requireValue("previousContent", previousContent);

        const currentLines = formatPromptContentLines(type, currentContent);
        if (previousContent === null) {
            return buildInitialSideBySideRows(currentLines);
        }

        const previousLines = formatPromptContentLines(type, previousContent);
        const operations = buildDiffOperations(previousLines, currentLines);
        const ranges = findChangedRanges(operations);
        if (ranges.length === 0) {
            return [{ type: "info", text: "No content changes between versions." }];
        }

        const rows = [];
        ranges.forEach(range => {
            const rangeOperations = operations.slice(range.start, range.end + 1);
            rows.push({ type: "hunk-header", text: buildHunkHeader(rangeOperations) });
            rows.push(...buildSideBySideRowsForOperations(rangeOperations));
        });
        return rows;
    }

    const api = { buildPromptHistoryDiffRows };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = api;
    }

    globalScope.PromptHistoryDiff = api;
}(typeof window !== "undefined" ? window : globalThis));
