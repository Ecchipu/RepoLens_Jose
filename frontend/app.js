const repoPathInput = document.getElementById("repoPath");
const searchQueryInput = document.getElementById("searchQuery");
const contextLinesInput = document.getElementById("contextLines");

const searchButton = document.getElementById("searchButton");
const filesButton = document.getElementById("filesButton");
const statsButton = document.getElementById("statsButton");
const symbolsButton = document.getElementById("symbolsButton");

const summaryContainer = document.getElementById("summary");
const resultsContainer = document.getElementById("results");
const statusText = document.getElementById("statusText");


function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function getRepoPath() {
    return repoPathInput.value.trim();
}


function getSearchQuery() {
    return searchQueryInput.value.trim();
}


function getContextLines() {
    return contextLinesInput.value;
}


function setStatus(message) {
    statusText.textContent = message;
}


function clearPage() {
    summaryContainer.innerHTML = "";
    resultsContainer.innerHTML = "";
}


function showError(message) {
    resultsContainer.innerHTML = `
        <div class="error-state">
            ${escapeHTML(message)}
        </div>
    `;
}


async function requestJSON(endpoint, params) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${endpoint}?${queryString}`;

    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || `Request failed with status ${response.status}`);
    }

    return data;
}


function renderSummary(cards) {
    summaryContainer.innerHTML = cards.map(card => {
        return `
            <article class="stat-card">
                <span>${escapeHTML(card.label)}</span>
                <strong>${escapeHTML(card.value)}</strong>
            </article>
        `;
    }).join("");
}


function renderSearchResults(data) {
    renderSummary([
        {
            label: "Repository",
            value: data.repository,
        },
        {
            label: "Files scanned",
            value: data.files_scanned,
        },
        {
            label: "Lines scanned",
            value: data.lines_scanned,
        },
        {
            label: "Results found",
            value: data.results_found,
        },
    ]);

    if (data.results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                No results found for "${escapeHTML(data.query)}".
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = data.results.map(result => {
        const contextHTML = result.context.map(contextLine => {
            const marker = contextLine.is_match ? ">" : "";

            return `
                <div class="code-line ${contextLine.is_match ? "match" : ""}">
                    <span class="marker">${marker}</span>
                    <span class="line-number">${contextLine.line_number}</span>
                    <span class="line-code">${escapeHTML(contextLine.line)}</span>
                </div>
            `;
        }).join("");

        return `
            <article class="result-card">
                <div class="result-path">
                    ${escapeHTML(result.path)}:${result.line_number}
                </div>

                <div class="code-block">
                    ${contextHTML}
                </div>
            </article>
        `;
    }).join("");
}


function renderFiles(data) {
    renderSummary([
        {
            label: "Repository",
            value: data.repository,
        },
        {
            label: "Files found",
            value: data.files_found,
        },
    ]);

    if (data.files.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                No supported files found.
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = `
        <div class="file-list">
            ${data.files.map(file => {
                return `
                    <div class="file-row">
                        <code>${escapeHTML(file.path)}</code>
                        <span>${escapeHTML(file.line_count)} lines</span>
                    </div>
                `;
            }).join("")}
        </div>
    `;
}


function renderStats(data) {
    renderSummary([
        {
            label: "Repository",
            value: data.repository,
        },
        {
            label: "Files scanned",
            value: data.files_scanned,
        },
        {
            label: "Lines scanned",
            value: data.lines_scanned,
        },
    ]);

    resultsContainer.innerHTML = `
        <div class="empty-state">
            RepoLens scanned ${escapeHTML(data.files_scanned)} file(s)
            and ${escapeHTML(data.lines_scanned)} line(s) of code.
        </div>
    `;
}


function renderSymbols(data) {
    renderSummary([
        {
            label: "Repository",
            value: data.repository,
        },
        {
            label: "Python files",
            value: data.python_files_analyzed,
        },
        {
            label: "Symbols found",
            value: data.symbols_found,
        },
        {
            label: "Imports found",
            value: data.imports_found,
        },
    ]);

    if (data.files.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                No Python files found to analyze.
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = data.files.map(file => {
        const symbolsHTML = file.symbols.length === 0
            ? `<p class="muted-text">No functions or classes found.</p>`
            : file.symbols.map(symbol => {
                return `
                    <div class="symbol-row">
                        <span class="symbol-type">${escapeHTML(symbol.type)}</span>
                        <code>${escapeHTML(symbol.name)}</code>
                        <span>Line ${escapeHTML(symbol.line_number)}</span>
                    </div>
                `;
            }).join("");

        const importsHTML = file.imports.length === 0
            ? `<p class="muted-text">No imports found.</p>`
            : file.imports.map(importItem => {
                if (importItem.type === "from_import") {
                    return `
                        <div class="symbol-row">
                            <span class="symbol-type">from import</span>
                            <code>from ${escapeHTML(importItem.module)} import ${escapeHTML(importItem.name)}</code>
                            <span>Line ${escapeHTML(importItem.line_number)}</span>
                        </div>
                    `;
                }

                return `
                    <div class="symbol-row">
                        <span class="symbol-type">import</span>
                        <code>${escapeHTML(importItem.module)}</code>
                        <span>Line ${escapeHTML(importItem.line_number)}</span>
                    </div>
                `;
            }).join("");

        const parseErrorHTML = file.parse_error
            ? `<div class="error-state">Parse error: ${escapeHTML(file.parse_error)}</div>`
            : "";

        return `
            <article class="result-card">
                <div class="result-path">
                    ${escapeHTML(file.path)}
                </div>

                <div class="symbol-section">
                    ${parseErrorHTML}

                    <h3>Symbols</h3>
                    ${symbolsHTML}

                    <h3>Imports</h3>
                    ${importsHTML}
                </div>
            </article>
        `;
    }).join("");
}


async function runSearch() {
    const repoPath = getRepoPath();
    const query = getSearchQuery();
    const contextLines = getContextLines();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    if (!query) {
        showError("Please enter a search query.");
        return;
    }

    clearPage();
    setStatus("Searching...");

    try {
        const data = await requestJSON("/search", {
            repo_path: repoPath,
            query: query,
            context_lines: contextLines,
        });

        renderSearchResults(data);
        setStatus("Search complete.");
    } catch (error) {
        showError(error.message);
        setStatus("Search failed.");
    }
}


async function viewFiles() {
    const repoPath = getRepoPath();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    clearPage();
    setStatus("Loading files...");

    try {
        const data = await requestJSON("/files", {
            repo_path: repoPath,
        });

        renderFiles(data);
        setStatus("Files loaded.");
    } catch (error) {
        showError(error.message);
        setStatus("Could not load files.");
    }
}


async function viewStats() {
    const repoPath = getRepoPath();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    clearPage();
    setStatus("Loading stats...");

    try {
        const data = await requestJSON("/stats", {
            repo_path: repoPath,
        });

        renderStats(data);
        setStatus("Stats loaded.");
    } catch (error) {
        showError(error.message);
        setStatus("Could not load stats.");
    }
}


async function viewSymbols() {
    const repoPath = getRepoPath();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    clearPage();
    setStatus("Loading symbols...");

    try {
        const data = await requestJSON("/symbols", {
            repo_path: repoPath,
        });

        renderSymbols(data);
        setStatus("Symbols loaded.");
    } catch (error) {
        showError(error.message);
        setStatus("Could not load symbols.");
    }
}


searchButton.addEventListener("click", runSearch);
filesButton.addEventListener("click", viewFiles);
statsButton.addEventListener("click", viewStats);
symbolsButton.addEventListener("click", viewSymbols);

searchQueryInput.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        runSearch();
    }
});