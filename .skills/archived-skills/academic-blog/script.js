    (function () {
        var lightbox = document.getElementById("image-lightbox");
        var lightboxImg = document.getElementById("image-lightbox-img");
        var lightboxVideo = document.getElementById("image-lightbox-video");
        var lightboxClose = document.getElementById("image-lightbox-close");
        var lightboxShell = lightbox ? lightbox.querySelector(".image-lightbox-shell") : null;
        var lightboxTitle = document.getElementById("image-lightbox-title");
        var lightboxKind = document.getElementById("image-lightbox-kind");
        var lightboxDescription = document.getElementById("image-lightbox-description");
        var lightboxPrev = document.getElementById("image-lightbox-prev");
        var lightboxNext = document.getElementById("image-lightbox-next");
        var zoomableLinks = document.querySelectorAll(".zoomable-image-link");
        var zoomableVideos = document.querySelectorAll(".demo-shot-media");
        if (lightbox && lightboxImg && lightboxVideo && lightboxClose && lightboxShell && lightboxTitle && lightboxKind && lightboxDescription && lightboxPrev && lightboxNext && lightbox.showModal) {
            var demoVideoEntries = [];
            var activeVideoIndex = -1;

            function readableName(href) {
                var filename = href.split("/").pop() || "";
                try {
                    filename = decodeURIComponent(filename);
                } catch (error) {}
                return filename;
            }

            function truncateText(text, maxLength) {
                if (!text || text.length <= maxLength) return text;
                return text.slice(0, maxLength - 1).trimEnd() + "…";
            }

            function normalizeSummaryText(text) {
                return (text || "")
                    .replace(/\s+/g, " ")
                    .replace(/\s*\/\s*/g, " / ")
                    .trim();
            }

            function setLightboxDescriptionText(text) {
                if (!text) {
                    lightboxDescription.hidden = true;
                    lightboxDescription.textContent = "";
                    return;
                }
                lightboxDescription.hidden = false;
                lightboxDescription.textContent = text;
            }

            function setLightboxMeta(kind, href, altText, descriptionText) {
                var fallback = readableName(href) || "放大预览";
                lightboxKind.textContent = kind;
                lightboxTitle.textContent = altText || fallback;
                setLightboxDescriptionText(descriptionText || "");
            }

            function updateLightboxNav() {
                var hasVideoRange = activeVideoIndex >= 0 && demoVideoEntries.length > 0;
                lightboxPrev.disabled = !hasVideoRange || activeVideoIndex <= 0;
                lightboxNext.disabled = !hasVideoRange || activeVideoIndex >= demoVideoEntries.length - 1;
            }

            function describeDemoFigure(figure) {
                if (!figure) return "";
                var traceThinking = figure.querySelector(".trace-thinking");
                if (traceThinking) {
                    var traceMeta = figure.querySelector(".trace-meta");
                    return truncateText(
                        normalizeSummaryText(
                            traceThinking.textContent + (traceMeta ? " / " + traceMeta.textContent : "")
                        ),
                        220
                    );
                }
                var summaryText = figure.querySelector("figcaption > span");
                if (!summaryText) return "";
                return truncateText(normalizeSummaryText(summaryText.textContent), 220);
            }

            function ensureMediaChrome() {
                return;
            }

            function resetLightboxMedia() {
                lightboxImg.removeAttribute("src");
                lightboxImg.removeAttribute("alt");
                lightboxImg.hidden = true;
                lightboxVideo.pause();
                lightboxVideo.hidden = true;
                lightboxVideo.removeAttribute("src");
                lightboxVideo.load();
                lightboxTitle.textContent = "放大预览";
                lightboxKind.textContent = "Media";
                setLightboxDescriptionText("");
                activeVideoIndex = -1;
                updateLightboxNav();
            }

            function closeLightbox() {
                if (lightbox.open) lightbox.close();
                resetLightboxMedia();
            }

            function openImageLightbox(href, altText) {
                resetLightboxMedia();
                lightboxImg.hidden = false;
                lightboxImg.src = href;
                lightboxImg.alt = altText || "";
                setLightboxMeta("Image", href, altText, "");
                if (!lightbox.open) lightbox.showModal();
            }

            function openVideoLightbox(href, titleText, descriptionText, kindText) {
                resetLightboxMedia();
                lightboxVideo.hidden = false;
                lightboxVideo.src = href;
                setLightboxMeta(kindText || "Video", href, titleText || "", descriptionText || "");
                if (!lightbox.open) lightbox.showModal();
                var playPromise = lightboxVideo.play();
                if (playPromise && typeof playPromise.catch === "function") {
                    playPromise.catch(function () {});
                }
            }

            function openVideoByIndex(index) {
                var entry = demoVideoEntries[index];
                if (!entry) return;
                openVideoLightbox(entry.href, entry.title, entry.description, entry.kind);
                activeVideoIndex = index;
                updateLightboxNav();
            }

            zoomableLinks.forEach(function (link) {
                link.addEventListener("click", function (event) {
                    var img = link.querySelector("img");
                    var href = link.getAttribute("href") || "";
                    event.preventDefault();
                    openImageLightbox(href, img ? (img.getAttribute("alt") || "") : "");
                });
            });

            zoomableVideos.forEach(function (media) {
                var video = media.querySelector("video");
                var source = video ? video.querySelector("source") : null;
                var figure = media.closest(".demo-shot");
                var group = media.closest(".demo-group");
                var captionTitle = figure ? figure.querySelector("figcaption strong") : null;
                var href = source ? source.getAttribute("src") : "";
                var titleText = captionTitle ? captionTitle.textContent.trim() : (video ? video.getAttribute("aria-label") : "");
                var descriptionText = describeDemoFigure(figure);
                var kindText = group ? (group.getAttribute("data-lightbox-kind") || "Video") : "Video";
                var chipText = group ? (group.getAttribute("data-demo-chip") || "") : "";
                if (!video || !href) return;
                ensureMediaChrome(media, chipText);
                var entryIndex = demoVideoEntries.push({
                    href: href,
                    title: titleText,
                    description: descriptionText,
                    kind: kindText
                }) - 1;
                if (!media.hasAttribute("tabindex")) media.setAttribute("tabindex", "0");
                if (!media.hasAttribute("role")) media.setAttribute("role", "button");
                if (!media.hasAttribute("aria-label")) {
                    media.setAttribute("aria-label", (video.getAttribute("aria-label") || "放大查看视频") + "，点击放大");
                }
                media.addEventListener("click", function () {
                    openVideoByIndex(entryIndex);
                });
                media.addEventListener("keydown", function (event) {
                    if (event.key !== "Enter" && event.key !== " ") return;
                    event.preventDefault();
                    openVideoByIndex(entryIndex);
                });
            });

            var demoCaptions = document.querySelectorAll(".demo-shot figcaption");

            function parseGuiTraceSteps(text) {
                var normalized = (text || "").replace(/\\"/g, '"');
                var pattern = /"thinking":\s*"([\s\S]*?)"\s*"action":\s*"([\s\S]*?)"(?:,\s*"x":\s*([-\d.]+),\s*"y":\s*([-\d.]+)|,\s*"text":\s*"([\s\S]*?)")?/g;
                var steps = [];
                var match;

                while ((match = pattern.exec(normalized))) {
                    steps.push({
                        thinking: (match[1] || "").trim(),
                        action: (match[2] || "").trim(),
                        x: match[3] || "",
                        y: match[4] || "",
                        text: (match[5] || "").trim()
                    });
                }

                return steps;
            }

            function appendGuiTraceCard(caption, steps) {
                if (!steps.length) return;

                caption.classList.add("trace-enhanced");
                var card = document.createElement("div");
                card.className = "trace-card";

                var kicker = document.createElement("p");
                kicker.className = "trace-kicker";
                kicker.textContent = "CUA Operation";
                card.appendChild(kicker);

                steps.forEach(function (step, index) {
                    var item = document.createElement("div");
                    item.className = "trace-step";

                    var head = document.createElement("div");
                    head.className = "trace-step-head";

                    var diamond = document.createElement("span");
                    diamond.className = "trace-step-index";
                    var diamondLabel = document.createElement("span");
                    diamondLabel.textContent = String(index + 1);
                    diamond.appendChild(diamondLabel);
                    head.appendChild(diamond);

                    var thinkingLabel = document.createElement("p");
                    thinkingLabel.className = "trace-label";
                    thinkingLabel.textContent = "Thinking";
                    head.appendChild(thinkingLabel);
                    item.appendChild(head);

                    var thinking = document.createElement("p");
                    thinking.className = "trace-thinking";
                    thinking.textContent = step.thinking;
                    item.appendChild(thinking);

                    var meta = document.createElement("div");
                    meta.className = "trace-meta";

                    var actionInline = document.createElement("span");
                    actionInline.className = "trace-inline";
                    var actionKey = document.createElement("strong");
                    actionKey.textContent = "Action";
                    actionInline.appendChild(actionKey);
                    actionInline.appendChild(document.createTextNode(step.action));
                    meta.appendChild(actionInline);

                    if (step.text) {
                        var textInline = document.createElement("span");
                        textInline.className = "trace-inline";
                        var textKey = document.createElement("strong");
                        textKey.textContent = "Text";
                        textInline.appendChild(textKey);
                        textInline.appendChild(document.createTextNode(step.text));
                        meta.appendChild(textInline);
                    } else if (step.x && step.y) {
                        var coordsInline = document.createElement("span");
                        coordsInline.className = "trace-inline";
                        var coordsKey = document.createElement("strong");
                        coordsKey.textContent = "Coords";
                        coordsInline.appendChild(coordsKey);
                        coordsInline.appendChild(document.createTextNode(step.x + ", " + step.y));
                        meta.appendChild(coordsInline);
                    }

                    item.appendChild(meta);
                    card.appendChild(item);
                });

                caption.appendChild(card);
            }

            demoCaptions.forEach(function (caption) {
                var summaryText = caption.querySelector("span");
                var shot = caption.closest(".demo-shot");
                var isGui = !!caption.closest(".demo-group.gui");
                var isGeneral = !!caption.closest(".demo-group.general");
                var isClean = !!caption.closest(".demo-group.clean");
                if (!summaryText) {
                    if (shot && (isGui || isGeneral || isClean)) {
                        shot.classList.add("compact-shot");
                    }
                    return;
                }
                var text = summaryText.textContent || "";
                var hasRawTrace = text.indexOf('"thinking":') !== -1 || text.indexOf('"action":') !== -1;
                if (hasRawTrace && isGui) {
                    appendGuiTraceCard(caption, parseGuiTraceSteps(text));
                    return;
                }
                if (hasRawTrace) return;
                if (shot && (isGui || isGeneral || isClean)) {
                    shot.classList.add("compact-shot");
                }

                if (!isClean && !isGeneral && !isGui) {
                    return;
                }

                caption.classList.add("summary-preview");

                requestAnimationFrame(function () {
                    var needsToggle = isClean || isGeneral || (summaryText.scrollHeight > summaryText.clientHeight + 2);
                    if (!needsToggle) {
                        caption.classList.remove("summary-preview");
                        return;
                    }

                    var toggle = document.createElement("button");
                    toggle.type = "button";
                    toggle.className = "demo-caption-toggle";
                    toggle.textContent = (isClean || isGeneral) ? "Read more" : "查看更多";
                    toggle.setAttribute("aria-expanded", "false");
                    toggle.addEventListener("click", function () {
                        var expanded = caption.classList.toggle("summary-expanded");
                        caption.classList.toggle("summary-preview", !expanded);
                        if (isClean || isGeneral) {
                            toggle.textContent = expanded ? "Collapse" : "Read more";
                        } else {
                            toggle.textContent = expanded ? "收起" : "查看更多";
                        }
                        toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
                    });
                    caption.appendChild(toggle);
                });
            });

            var guiTraceCaptions = document.querySelectorAll(".demo-group.gui figcaption");
            guiTraceCaptions.forEach(function (caption) {
                if (caption.querySelector(".trace-card")) return;
                var rawTrace = caption.querySelector(":scope > span");
                if (!rawTrace) return;
                var steps = parseGuiTraceSteps(rawTrace.textContent || "");
                if (!steps.length) return;
                appendGuiTraceCard(caption, steps);
            });

            var guiComparisonTable = document.querySelector(".gui-comparison-table");
            var guiAdditionalDivider = document.querySelector(".gui-additional-divider");
            var guiAdditionalGrid = document.querySelector(".gui-additional-grid");
            if (guiComparisonTable && guiAdditionalDivider && guiAdditionalGrid) {
                var guiRows = Array.prototype.slice.call(guiComparisonTable.querySelectorAll("tbody tr"));
                if (guiRows.length > 2) {
                    guiRows.slice(2).forEach(function (row) {
                        row.classList.add("gui-row-collapsed");
                    });
                }
                guiAdditionalDivider.classList.add("is-collapsed");
                guiAdditionalGrid.classList.add("is-collapsed");

                var guiToggleWrap = document.createElement("div");
                guiToggleWrap.className = "demo-grid-toggle-wrap inside-gallery";

                var guiToggle = document.createElement("button");
                guiToggle.type = "button";
                guiToggle.className = "demo-grid-toggle";
                guiToggle.textContent = "展开更多样本";
                guiToggle.setAttribute("aria-expanded", "false");

                var guiEndToggleWrap = document.createElement("div");
                guiEndToggleWrap.className = "demo-grid-toggle-wrap inside-gallery gui-comparison-end-toggle is-collapsed";

                var guiEndToggle = document.createElement("button");
                guiEndToggle.type = "button";
                guiEndToggle.className = "demo-grid-toggle";
                guiEndToggle.textContent = "收起后续样本";
                guiEndToggle.setAttribute("aria-expanded", "true");

                function setGuiExpanded(expanded) {
                    if (guiRows.length > 2) {
                        guiRows.slice(2).forEach(function (row) {
                            row.classList.toggle("gui-row-collapsed", !expanded);
                        });
                    }
                    guiAdditionalDivider.classList.toggle("is-collapsed", !expanded);
                    guiAdditionalGrid.classList.toggle("is-collapsed", !expanded);
                    guiToggleWrap.classList.toggle("is-collapsed", expanded);
                    guiEndToggleWrap.classList.toggle("is-collapsed", !expanded);
                    guiToggle.setAttribute("aria-expanded", expanded ? "true" : "false");
                    guiEndToggle.setAttribute("aria-expanded", expanded ? "true" : "false");
                }

                guiToggle.addEventListener("click", function () {
                    setGuiExpanded(true);
                });

                guiEndToggle.addEventListener("click", function () {
                    setGuiExpanded(false);
                    guiComparisonTable.scrollIntoView({ behavior: "smooth", block: "start" });
                });

                guiToggleWrap.appendChild(guiToggle);
                guiEndToggleWrap.appendChild(guiEndToggle);
                var toggleRow = document.createElement("tr");
                toggleRow.className = "gui-comparison-toggle-row";
                var toggleCell = document.createElement("td");
                toggleCell.colSpan = 2;
                toggleCell.appendChild(guiToggleWrap);
                toggleRow.appendChild(toggleCell);
                guiRows[1].insertAdjacentElement("afterend", toggleRow);
                guiAdditionalGrid.insertAdjacentElement("afterend", guiEndToggleWrap);
            }

            var generalGrid = document.querySelector(".demo-grid.general");
            if (generalGrid) {
                var generalShots = Array.prototype.slice.call(generalGrid.querySelectorAll(".demo-shot"));
                if (generalShots.length > 3) {
                    generalGrid.classList.add("is-collapsed");

                    var generalToggleWrap = document.createElement("div");
                    generalToggleWrap.className = "demo-grid-toggle-wrap inside-gallery";

                    var generalToggle = document.createElement("button");
                    generalToggle.type = "button";
                    generalToggle.className = "demo-grid-toggle";
                    generalToggle.textContent = "展开更多样本";
                    generalToggle.setAttribute("aria-expanded", "false");

                    generalToggle.addEventListener("click", function () {
                        var expanded = generalGrid.classList.toggle("is-expanded");
                        generalGrid.classList.toggle("is-collapsed", !expanded);
                        generalToggle.textContent = expanded ? "收起后续样本" : "展开更多样本";
                        generalToggle.setAttribute("aria-expanded", expanded ? "true" : "false");
                    });

                    generalToggleWrap.appendChild(generalToggle);
                    generalGrid.appendChild(generalToggleWrap);
                }
            }

            var cleanGrid = document.querySelector(".demo-grid.clean");
            if (cleanGrid) {
                var cleanShots = Array.prototype.slice.call(cleanGrid.querySelectorAll(".demo-shot"));
                if (cleanShots.length > 6) {
                    cleanGrid.classList.add("is-collapsed");

                    var cleanToggleWrap = document.createElement("div");
                    cleanToggleWrap.className = "demo-grid-toggle-wrap inside-gallery";

                    var cleanToggle = document.createElement("button");
                    cleanToggle.type = "button";
                    cleanToggle.className = "demo-grid-toggle";
                    cleanToggle.textContent = "展开更多样本";
                    cleanToggle.setAttribute("aria-expanded", "false");

                    cleanToggle.addEventListener("click", function () {
                        var expanded = cleanGrid.classList.toggle("is-expanded");
                        cleanGrid.classList.toggle("is-collapsed", !expanded);
                        cleanToggle.textContent = expanded ? "收起后续样本" : "展开更多样本";
                        cleanToggle.setAttribute("aria-expanded", expanded ? "true" : "false");
                    });

                    cleanToggleWrap.appendChild(cleanToggle);
                    cleanGrid.appendChild(cleanToggleWrap);
                }
            }

            lightboxPrev.addEventListener("click", function () {
                if (activeVideoIndex > 0) {
                    openVideoByIndex(activeVideoIndex - 1);
                }
            });

            lightboxNext.addEventListener("click", function () {
                if (activeVideoIndex >= 0 && activeVideoIndex < demoVideoEntries.length - 1) {
                    openVideoByIndex(activeVideoIndex + 1);
                }
            });

            document.addEventListener("keydown", function (event) {
                if (!lightbox.open || lightboxVideo.hidden) return;
                if (event.key === "ArrowLeft" && !lightboxPrev.disabled) {
                    event.preventDefault();
                    openVideoByIndex(activeVideoIndex - 1);
                } else if (event.key === "ArrowRight" && !lightboxNext.disabled) {
                    event.preventDefault();
                    openVideoByIndex(activeVideoIndex + 1);
                }
            });

            lightboxClose.addEventListener("click", closeLightbox);
            lightbox.addEventListener("click", function (event) {
                if (!lightboxShell.contains(event.target)) closeLightbox();
            });
            lightbox.addEventListener("close", function () {
                resetLightboxMedia();
            });
        }

        var summary = document.getElementById("summary");
        if (!summary) return;

        var expandedHeight = 0;
        var revealThreshold = 0;
        var isCollapsed = summary.classList.contains('is-collapsed');

        function measureSummary() {
            var wasCollapsed = summary.classList.contains('is-collapsed');
            summary.classList.remove('is-collapsed');
            summary.style.maxHeight = 'none';
            expandedHeight = summary.scrollHeight;
            summary.style.maxHeight = expandedHeight + 'px';
            revealThreshold = Math.min(Math.max(window.innerHeight * 0.04, 20), 48);
            if (wasCollapsed) summary.classList.add('is-collapsed');
        }

        function setCollapsed(next) {
            if (next === isCollapsed) return;
            isCollapsed = next;
            if (isCollapsed) {
                summary.classList.add('is-collapsed');
            } else {
                summary.classList.remove('is-collapsed');
                summary.style.maxHeight = expandedHeight + 'px';
            }
        }

        function updateSummaryState() {
            setCollapsed(window.scrollY < revealThreshold);
        }

        measureSummary();
        updateSummaryState();
        window.addEventListener('scroll', updateSummaryState, { passive: true });
        window.addEventListener('resize', function () {
            measureSummary();
            updateSummaryState();
        });
    })();

    (function () {
        var toggle = document.getElementById("contact-toggle");
        var panel = document.getElementById("contact-panel");
        if (!toggle || !panel) return;

        toggle.addEventListener("click", function () {
            var willOpen = panel.classList.contains("is-collapsed");
            panel.classList.toggle("is-collapsed", !willOpen);
            toggle.setAttribute("aria-expanded", String(willOpen));
        });
    })();
