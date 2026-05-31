(function () {
  // --- Core Redirect & Interception Logic ---


  // --- Helpers ---

  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2)
      return decodeURIComponent(parts.pop().split(";").shift());
    return "";
  };

  const setCookie = (name, value, days) => {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie =
      name +
      "=" +
      encodeURIComponent(value) +
      "; expires=" +
      expires +
      "; path=/";
  };

  const applyInterception = () => {
    if (window._playgroundIntercepted) return;
    window._playgroundIntercepted = true;

    const originalFetch = window.fetch;

    // Hard Monkey-patch Fetch (non-writable to prevent framework overrides)
    const customFetch = async function (...args) {
      let [resource, config] = args;
      const urlStr = typeof resource === "string" ? resource : resource?.url;

      if (
        urlStr &&
        (urlStr.includes("example.com") || urlStr.includes("api.example.com"))
      ) {
        const apiBase = getCookie("api_url")?.replace(/\/$/, "");
        const apiKey = getCookie("api_key");

        if (apiBase) {
          const normalizedBase = apiBase.startsWith("http")
            ? apiBase
            : `http://${apiBase}`;
          const newUrl = urlStr.replace(
            /https?:\/\/(api\.)?example\.com/,
            normalizedBase,
          );

          if (typeof resource === "string") {
            resource = newUrl;
          } else {
            resource = new Request(newUrl, resource);
          }

          if (apiKey) {
            config = config || {};
            config.headers = config.headers || {};
            if (config.headers instanceof Headers) {
              config.headers.set("x-api-key", apiKey);
            } else {
              config.headers["x-api-key"] = apiKey;
            }
          }

          // Fix double-escaped sequences (Mintlify playground sends \\n instead of real newlines)
          if (config && config.body && typeof config.body === "string") {
            try {
              const _fixEscapes = (v) => {
                if (typeof v === "string") return v.replace(/\\n/g, "\n").replace(/\\t/g, "\t").replace(/\\r/g, "\r");
                if (Array.isArray(v)) return v.map(_fixEscapes);
                if (v && typeof v === "object") { const r = {}; for (const k in v) r[k] = _fixEscapes(v[k]); return r; }
                return v;
              };
              config.body = JSON.stringify(_fixEscapes(JSON.parse(config.body)));
            } catch (e) {}
          }

          console.log("Playground Redirect:", urlStr, "->", newUrl);
          return originalFetch(resource, config);
        }
      }
      return originalFetch(...args);
    };

    try {
      Object.defineProperty(window, "fetch", {
        value: customFetch,
        configurable: false,
        writable: false,
      });
    } catch (e) {
      window.fetch = customFetch;
    }

    // XHR Interception
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
      if (
        typeof url === "string" &&
        (url.includes("example.com") || url.includes("api.example.com"))
      ) {
        const apiBase = getCookie("api_url")?.replace(/\/$/, "");
        if (apiBase) {
          const normalizedBase = apiBase.startsWith("http")
            ? apiBase
            : `http://${apiBase}`;
          url = url.replace(/https?:\/\/(api\.)?example\.com/, normalizedBase);
          console.log("XHR Redirect:", url);
        }
      }
      return originalOpen.call(this, method, url, ...rest);
    };

    // XHR body fix: unescape literal \n sequences
    const originalSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function (body) {
      if (body && typeof body === "string") {
        try {
          const _fixEscapes = (v) => {
            if (typeof v === "string") return v.replace(/\\n/g, "\n").replace(/\\t/g, "\t").replace(/\\r/g, "\r");
            if (Array.isArray(v)) return v.map(_fixEscapes);
            if (v && typeof v === "object") { const r = {}; for (const k in v) r[k] = _fixEscapes(v[k]); return r; }
            return v;
          };
          body = JSON.stringify(_fixEscapes(JSON.parse(body)));
        } catch (e) {}
      }
      return originalSend.call(this, body);
    };
  };

  applyInterception();

  // --- Hide base URL in endpoint bars ---
  function hideBaseUrl() {
    // Target font-mono elements inside endpoint bar containers
    document
      .querySelectorAll(".font-mono.min-w-max, .font-mono.cursor-pointer")
      .forEach((el) => {
        const text = el.textContent.trim();
        // Only hide if it looks like a base URL (not a route segment)
        if (
          text.match(/^https?:\/\//) ||
          text.includes("example.com") ||
          text.includes("api.")
        ) {
          el.style.setProperty("display", "none", "important");
        }
      });
  }
  hideBaseUrl();

  // --- UI and Styling ---
  // Inject CSS to hide auth fields globally and instantly (ONLY when cookies are configured)
  const _hasAuthCookies = getCookie("api_url") && getCookie("api_key");
  if (_hasAuthCookies && !document.getElementById("auth-hide-styles")) {
    const style = document.createElement("style");
    style.id = "auth-hide-styles";
    style.textContent = `
      /* Deep hide header/auth containers in playground and modals */
      .api-playground-param:has(input[placeholder*="SUA_SENHA_SECRETA"]),
      .api-playground-param:has(input[id*="x-api-key"]),
      div[class*="ParamField"]:has(input[placeholder*="SUA_SENHA_SECRETA"]),
      div[class*="ParamField"]:has(input[id*="x-api-key"]),
      .flex.flex-row.gap-4:has(input[placeholder*="SUA_SENHA_SECRETA"]) {
        display: none !important;
      }
      /* Empty State styles */
      .playground-empty-state {
        padding: 2.5rem 1.5rem;
        border: 1px solid rgba(124, 27, 194, 0.2);
        border-radius: 1.25rem;
        text-align: center;
        background: #0c0b10 !important;
        margin-top: 2rem;
        backdrop-blur: 10px;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
      }
      .dark .playground-empty-state {
        border-color: rgba(124, 27, 194, 0.15);
        background: #0c0b10 !important;
      }
    `;
    document.head.appendChild(style);
  }

  // Check if the URL contains playground=open
  function shouldHideButton() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get("playground") === "open";
  }

  // Function to disable/enable body scroll with multiple methods
  function toggleBodyScroll() {
    if (shouldHideButton()) {
      // Save current scroll position
      const scrollY = window.scrollY;

      // Disable body scroll with multiple approaches
      document.body.style.setProperty("overflow", "hidden", "important");
      document.body.style.setProperty("position", "fixed", "important");
      document.body.style.setProperty("top", `-${scrollY}px`, "important");
      document.body.style.setProperty("width", "100%", "important");
      document.documentElement.style.setProperty(
        "overflow",
        "hidden",
        "important",
      );

      // Prevent touch scroll and wheel events
      document.addEventListener("touchmove", preventScroll, { passive: false });
      document.addEventListener("wheel", preventScroll, { passive: false });
    } else {
      // Restore scroll position
      const scrollY = document.body.style.top;

      // Enable body scroll
      document.body.style.removeProperty("overflow");
      document.body.style.removeProperty("position");
      document.body.style.removeProperty("top");
      document.body.style.removeProperty("width");
      document.documentElement.style.removeProperty("overflow");

      // Restore scroll position
      if (scrollY) {
        window.scrollTo(0, parseInt(scrollY || "0") * -1);
      }

      // Remove event listeners
      document.removeEventListener("touchmove", preventScroll);
      document.removeEventListener("wheel", preventScroll);
    }
  }

  // Prevent scroll event - allow scrolling only within playground containers
  function preventScroll(e) {
    // Check if the scroll is happening within the playground modal/container
    const playgroundSelectors = [
      ".grid.grid-cols-1.lg\\:grid-cols-5", // Main playground grid
      '[class*="grid"][class*="cols"]', // Any grid container
      '[class*="space-y"]', // Space-y containers
      '[class*="overflow"]', // Overflow containers
      ".api-playground-input",
      "#api-playground-input",
      '[class*="playground"]',
      '[data-testid*="playground"]',
      '[class*="scrollbar"]',
      '[class*="overflow-auto"]',
      '[class*="overflow-y-auto"]',
    ];

    // Check if target or any parent matches playground selectors
    let element = e.target;
    while (element && element !== document.body) {
      for (const selector of playgroundSelectors) {
        try {
          if (element.matches && element.matches(selector)) {
            // Allow scrolling within this element if it's scrollable
            const hasScroll = element.scrollHeight > element.clientHeight;
            if (hasScroll) {
              return; // Allow scroll
            }
          }
        } catch (err) {
          // Invalid selector, skip
        }
      }
      element = element.parentElement;
    }

    // If we're here, prevent the scroll
    e.preventDefault();
    e.stopPropagation();
  }

  function renameTryItButton() {
    const tryItButtons = document.querySelectorAll(
      '.tryit-button, [data-testid="try-it-button"]',
    );

    tryItButtons.forEach((button) => {
      const isInsidePlayground = !!button.closest(
        '[data-testid="api-playground-modal"]',
      );
      const hasAllCookies =
        getCookie("api_url") &&
        getCookie("api_key") &&
        getCookie("internal_secret");

      // "Send"/"Enviar" inside the playground → hide if no cookies
      if (isInsidePlayground && !hasAllCookies) {
        button.style.setProperty("display", "none", "important");
        return;
      }

      // "Try it"/"Testar" on the page → always visible
      if (button.style.display === "none") {
        button.style.removeProperty("display");
      }

      // Update text while preserving the icon (SVG)
      let targetSpan = button.querySelector("span");
      let currentText = (
        targetSpan ? targetSpan.textContent : button.textContent
      ).trim();

      if (currentText === "Send" || currentText === "Try it") {
        const isSend = currentText === "Send";
        const newText = isSend ? "Enviar" : "Testar";

        if (targetSpan) {
          targetSpan.textContent = newText;
        } else {
          // Fallback: search for text nodes to avoid killing the SVG
          for (let node of button.childNodes) {
            if (
              node.nodeType === Node.TEXT_NODE &&
              node.textContent.trim() === currentText
            ) {
              node.textContent = newText;
              break;
            }
          }
        }

        button.setAttribute("aria-label", newText);
        // Remove fixed width that squeezes the icon
        button.classList.remove("w-20");
        button.style.minWidth = isSend ? "90px" : "85px"; // Give it enough room
      }
    });
  }

  // Function to translate UI elements to Portuguese
  function translateUI() {
    // Target all possible "On this page" and "Search" occurrences
    const selectors = [
      "button span", // Mobile TOC button
      ".text-xs.font-semibold.uppercase.tracking-wide.text-gray-900.dark\\:text-white", // Desktop sidebar heading
      ".text-sm.font-semibold.text-gray-900.dark\\:text-white", // Alternative sidebar heading
      ".truncate", // General truncate class used in search bar
      "#search-bar-entry div", // Specific content inside search bar
      // Context menu translations
      ".text-sm.font-medium.text-gray-800.dark\\:text-gray-300", // Menu titles
      ".text-xs.text-gray-600.dark\\:text-gray-400", // Menu descriptions
    ];

    selectors.forEach((selector) => {
      document.querySelectorAll(selector).forEach((el) => {
        const text = el.textContent.trim();
        if (text === "On this page") {
          el.textContent = "Nesta página";
        } else if (text === "Search...") {
          el.textContent = "Buscar...";
        } else if (text === "Copy page") {
          el.textContent = "Copiar";
        } else if (text === "Copy page as Markdown for LLMs") {
          el.textContent = "Copiar como Markdown para LLMs";
        } else if (text === "Open in ChatGPT") {
          el.textContent = "Abrir no ChatGPT";
        } else if (text.includes("Ask questions about this page")) {
          el.textContent = "Fazer perguntas sobre esta página";
        } else if (text === "Open in Claude") {
          el.textContent = "Abrir no Claude";
        }
      });
    });

    // Also check buttons directly and inputs
    document.querySelectorAll("button, input").forEach((el) => {
      const text = el.textContent.trim();
      if (text === "On this page") {
        el.textContent = "Nesta página";
      } else if (text === "Copy page") {
        const span = el.querySelector("span");
        if (span) span.textContent = "Copiar";
        else el.textContent = "Copiar";
      }

      if (el.placeholder === "Search...") {
        el.placeholder = "Buscar...";
      }
      if (el.getAttribute("aria-label") === "Open search") {
        el.setAttribute("aria-label", "Abrir busca");
      }
      if (el.getAttribute("aria-label") === "Copy page") {
        el.setAttribute("aria-label", "Copiar");
      }
      if (el.getAttribute("aria-label") === "More actions") {
        el.setAttribute("aria-label", "Mais ações");
      }
    });
  }

  // Function to color only {railway_domain} text in purple
  function colorRailwayDomain() {
    // More specific targeting for the URL display element
    const selectors = [
      ".min-w-max.bg-transparent.text-sm.font-mono",
      ".min-w-max.font-mono",
      '[class*="min-w-max"]',
      ".text-sm.text-gray-600",
      ".dark\\:text-gray-400",
    ];

    // Try specific selectors first
    let found = false;
    selectors.forEach((selector) => {
      document.querySelectorAll(selector).forEach((el) => {
        // Skip code blocks
        if (el.closest('pre, code, [class*="shiki"], [class*="code-block"]')) {
          return;
        }

        if (el.textContent.includes("{railway_domain}")) {
          // Process this element
          processRailwayDomainNode(el);
          found = true;
        }
      });
    });

    // Fallback: scan all elements if not found with specific selectors
    if (!found) {
      document.querySelectorAll("*").forEach((el) => {
        // Skip code blocks
        if (el.closest('pre, code, [class*="shiki"], [class*="code-block"]')) {
          return;
        }

        // Only process text nodes directly
        Array.from(el.childNodes).forEach((node) => {
          if (
            node.nodeType === Node.TEXT_NODE &&
            node.textContent.includes("{railway_domain}")
          ) {
            processRailwayDomainTextNode(node);
          }
        });
      });
    }
  }

  // Helper to process element that contains {railway_domain}
  function processRailwayDomainNode(el) {
    Array.from(el.childNodes).forEach((node) => {
      if (
        node.nodeType === Node.TEXT_NODE &&
        node.textContent.includes("{railway_domain}")
      ) {
        processRailwayDomainTextNode(node);
      }
    });
  }

  // Helper to process a text node and wrap {railway_domain} in purple span
  function processRailwayDomainTextNode(node) {
    const text = node.textContent;
    const parts = text.split(/(\{railway_domain\})/g);

    if (parts.length > 1) {
      const fragment = document.createDocumentFragment();
      parts.forEach((part) => {
        if (part === "{railway_domain}") {
          const span = document.createElement("span");
          span.textContent = part;
          span.style.setProperty("color", "#7c1bc2", "important");
          span.style.fontWeight = "600"; // Make it slightly bolder
          fragment.appendChild(span);
        } else if (part) {
          fragment.appendChild(document.createTextNode(part));
        }
      });
      node.replaceWith(fragment);
    }
  }

  // --- Visual Copy Hijacking ---
  // Ensures that when the user clicks copy on a code block, they get the
  // visually injected values (URL/API Key) instead of the placeholders.
  function hijackCodeBlockCopy() {
    document
      .querySelectorAll('[data-testid="copy-code-button"]')
      .forEach((btn) => {
        if (btn.dataset.hijacked) return;
        btn.dataset.hijacked = "true";

        btn.addEventListener(
          "click",
          (e) => {
            // Find the corresponding code block
            const container =
              btn.closest(".code-group") || btn.closest("div:has(pre)");
            const codeBlock = container?.querySelector("pre");

            if (codeBlock) {
              e.preventDefault();
              e.stopPropagation();

              const textToCopy = codeBlock.innerText;
              navigator.clipboard.writeText(textToCopy).then(() => {
                // Provide visual feedback
                let tooltip = btn.parentElement.querySelector(
                  'div[class*="Tooltip"]',
                );

                // Fallback for non-class tooltips: find siblings with "Copy" text
                if (!tooltip) {
                  const siblings = Array.from(btn.parentElement.children);
                  tooltip = siblings.find((el) =>
                    el.textContent.includes("Copy"),
                  );
                }

                if (tooltip) {
                  const originalText = tooltip.textContent;
                  tooltip.textContent = "Copiado!";
                  setTimeout(() => {
                    tooltip.textContent = originalText;
                  }, 2000);
                }

                // Toggle icon classes if possible (Mintlify style)
                const icon = btn.querySelector("svg");
                if (icon) {
                  icon.style.color = "#22c55e"; // Success green
                  setTimeout(() => {
                    icon.style.color = "";
                  }, 2000);
                }
              });
            }
          },
          { capture: true },
        );
      });
  }

  // --- Configuration Handling ---

  // Flag to prevent mutation observer from overwriting inputs while user is typing
  let _configEditing = false;

  const loadConfigSettings = () => {
    // Never overwrite while the user is actively editing
    if (_configEditing) return;

    const urlInput = document.getElementById("api_url");
    const keyInput = document.getElementById("api_key");
    const secretInput = document.getElementById("internal_secret");

    const active = document.activeElement;

    // Helper: only set value if cookie has content OR input is still empty
    // This prevents clearing fields that the user has typed into but not saved yet
    const safeSet = (el, cookieVal) => {
      if (!el || el === active) return;
      if (cookieVal) {
        el.value = cookieVal;
      }
      // If cookie is empty but input already has content, do NOT clear it
    };

    safeSet(urlInput, getCookie("api_url"));
    safeSet(keyInput, getCookie("api_key"));
    safeSet(secretInput, getCookie("internal_secret"));
  };

  const setupConfigListeners = () => {
    const saveBtn = document.getElementById("btn_save");
    const clearBtn = document.getElementById("btn_clear");

    if (saveBtn && !saveBtn.dataset.listener) {
      saveBtn.onclick = () => {
        const urlVal = document.getElementById("api_url").value;
        const keyVal = document.getElementById("api_key").value;
        const secretVal = document.getElementById("internal_secret");
        const secretValContent = secretVal ? secretVal.value : "";

        setCookie("api_url", urlVal, 30);
        setCookie("api_key", keyVal, 30);
        setCookie("internal_secret", secretValContent, 30);

        // Force-reset the sync cache so code blocks re-render with new values
        _currentConfig = { url: "", key: "" };
        document.querySelectorAll("[data-synced]").forEach((el) => {
          delete el.dataset.synced;
        });

        // Inject auth-hiding CSS now that cookies exist
        if (!document.getElementById("auth-hide-styles")) {
          const authStyle = document.createElement("style");
          authStyle.id = "auth-hide-styles";
          authStyle.textContent = `
            .api-playground-param:has(input[placeholder*="SUA_SENHA_SECRETA"]),
            .api-playground-param:has(input[id*="x-api-key"]),
            div[class*="ParamField"]:has(input[placeholder*="SUA_SENHA_SECRETA"]),
            div[class*="ParamField"]:has(input[id*="x-api-key"]),
            .flex.flex-row.gap-4:has(input[placeholder*="SUA_SENHA_SECRETA"]) {
              display: none !important;
            }
          `;
          document.head.appendChild(authStyle);
        }

        // Trigger immediate re-sync
        syncCodeBlocks();
        syncPlaygroundUI();
        replaceApiTextInDOM();

        // Button feedback
        const span = saveBtn.querySelector("span");
        const originalText = span ? span.textContent : saveBtn.textContent;

        if (span) span.textContent = "Configurações salvas";
        else saveBtn.textContent = "Configurações salvas";

        saveBtn.disabled = true;
        saveBtn.classList.add("opacity-50", "cursor-not-allowed");

        setTimeout(() => {
          if (span) span.textContent = originalText;
          else saveBtn.textContent = originalText;
          saveBtn.disabled = false;
          saveBtn.classList.remove("opacity-50", "cursor-not-allowed");
        }, 3000);
      };
      saveBtn.dataset.listener = "true";
    }

    if (clearBtn && !clearBtn.dataset.listener) {
      clearBtn.onclick = () => {
        setCookie("api_url", "", -1);
        setCookie("api_key", "", -1);
        setCookie("internal_secret", "", -1);

        // Force-reset the sync cache
        _currentConfig = { url: "", key: "" };
        document.querySelectorAll("[data-synced]").forEach((el) => {
          delete el.dataset.synced;
        });

        // Remove auth-hiding CSS since cookies are gone
        const authStyle = document.getElementById("auth-hide-styles");
        if (authStyle) authStyle.remove();
        const flickerStyle = document.getElementById("zap-unlocked-no-flicker");
        if (flickerStyle) flickerStyle.remove();

        // Clear config page input fields
        ["api_url", "api_key", "internal_secret"].forEach((id) => {
          const el = document.getElementById(id);
          if (el) el.value = "";
        });

        // Clear hidden playground auth inputs (set by syncPlaygroundUI)
        // Must use React-compatible setter to actually update React state
        const reactSetter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype,
          "value",
        )?.set;
        document.querySelectorAll("input").forEach((input) => {
          const isAuthField =
            input.placeholder?.toLowerCase().includes("sua_senha_secreta") ||
            input.placeholder?.toLowerCase().includes("x-api-key") ||
            input.id.includes("x-api-key") ||
            input
              .getAttribute("aria-label")
              ?.toLowerCase()
              .includes("x-api-key") ||
            input.name?.toLowerCase().includes("x-api-key");
          if (isAuthField) {
            // Use React setter to properly clear the value
            if (reactSetter) {
              reactSetter.call(input, "");
            } else {
              input.value = "";
            }
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            // Un-hide the container if it was hidden by sync
            const container =
              input.closest(".api-playground-param") ||
              input.closest('[class*="ParamField"]') ||
              input.closest(".flex.flex-col.gap-2") ||
              input.closest(".flex.flex-row.gap-4") ||
              input.parentElement;
            if (container && container.dataset.hiddenBySync) {
              container.style.removeProperty("display");
              container.style.removeProperty("visibility");
              delete container.dataset.hiddenBySync;
            }
          }
        });

        // Re-sync code blocks with default values
        syncCodeBlocks();

        const originalText = clearBtn.textContent;
        clearBtn.textContent = "Cookies removidos";
        clearBtn.disabled = true;

        setTimeout(() => {
          clearBtn.textContent = originalText;
          clearBtn.disabled = false;
        }, 2000);
      };
      clearBtn.dataset.listener = "true";
    }
  };

  // --- Playground Interception & Sync ---

  // Continuous validation: if cookies are missing, clear any orphaned auth input values
  const cleanOrphanAuthInputs = () => {
    const hasAllCookies =
      getCookie("api_url") &&
      getCookie("api_key") &&
      getCookie("internal_secret");
    if (hasAllCookies) return; // Cookies are set, nothing to clean

    // Skip if we're on the config page
    if (
      document.getElementById("api_url") &&
      document.getElementById("api_key")
    )
      return;

    const reactSetter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      "value",
    )?.set;

    document.querySelectorAll("input").forEach((input) => {
      const isAuthField =
        input.placeholder?.toLowerCase().includes("sua_senha_secreta") ||
        input.placeholder?.toLowerCase().includes("x-api-key") ||
        input.placeholder?.toLowerCase().includes("enter x-api-key") ||
        input.id.includes("x-api-key") ||
        input.getAttribute("aria-label")?.toLowerCase().includes("x-api-key") ||
        input.name?.toLowerCase().includes("x-api-key");

      if (isAuthField && input.value) {
        if (reactSetter) {
          reactSetter.call(input, "");
        } else {
          input.value = "";
        }
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  };

  const syncPlaygroundUI = () => {
    // DO NOT hide fields if we are on the configuration page
    if (
      document.getElementById("api_url") &&
      document.getElementById("api_key")
    ) {
      return;
    }

    const apiKey = getCookie("api_key");
    const hasAllCookies =
      apiKey && getCookie("api_url") && getCookie("internal_secret");
    if (!hasAllCookies) return;

    // Helper to set value on React controlled inputs
    const setReactValue = (el, val) => {
      if (!el) return;
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        "value",
      ).set;
      if (setter) {
        setter.call(el, val);
      } else {
        el.value = val;
      }
      // Trigger all events to satisfy React/Mintlify validation
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      el.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true }));
      el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true }));
      el.dispatchEvent(new Event("blur", { bubbles: true }));
    };

    document.querySelectorAll("input").forEach((input) => {
      // Focus strictly on x-api-key
      const isAuthField =
        input.placeholder?.toLowerCase().includes("sua_senha_secreta") ||
        input.id.includes("x-api-key") ||
        input.getAttribute("aria-label")?.toLowerCase().includes("x-api-key") ||
        input
          .getAttribute("aria-label")
          ?.toLowerCase()
          .includes("enter x-api-key") ||
        input.name?.toLowerCase().includes("x-api-key");

      if (isAuthField) {
        if (input.value !== apiKey) {
          setReactValue(input, apiKey);
        }

        // Hide container
        const container =
          input.closest(".api-playground-param") ||
          input.closest('[class*="ParamField"]') ||
          input.closest(".flex.flex-col.gap-2") ||
          input.closest(".flex.flex-row.gap-4") ||
          input.parentElement;

        if (container) {
          container.style.setProperty("display", "none", "important");
          container.style.setProperty("visibility", "hidden", "important");
          container.dataset.hiddenBySync = "true";

          // Try to hide any auth-related accordion/section (Header, Authorization, Auth, etc.)
          let section = container.parentElement;
          const authKeywords = [
            "header",
            "authorization",
            "autenticação",
            "auth",
          ];
          while (section && section !== document.body) {
            const btn = section.querySelector('[role="button"]');
            if (btn) {
              const btnText = btn.textContent.toLowerCase();
              const btnLabel =
                btn.getAttribute("aria-label")?.toLowerCase() || "";
              if (
                authKeywords.some(
                  (kw) => btnText.includes(kw) || btnLabel.includes(kw),
                )
              ) {
                section.style.setProperty("display", "none", "important");
                section.dataset.hiddenBySync = "true";
                break;
              }
            }
            if (section.classList.contains("api-playground-modal")) break;
            section = section.parentElement;
          }
        }
      }
    });

    // Handle "Empty State" - if all param sections are hidden
    const playground = document.querySelector(
      '[data-testid="api-playground-modal"]',
    );
    if (playground) {
      const paramColumn = playground.querySelector(
        ".col-span-1.lg\\:col-span-3",
      );
      if (paramColumn) {
        const paramSections = paramColumn.querySelectorAll(
          ".space-y-2.mt-6 > div",
        );
        let visibleSections = 0;
        paramSections.forEach((s) => {
          if (s.style.display !== "none" && !s.dataset.hiddenBySync) {
            visibleSections++;
          }
        });

        const existingEmptyMsg = paramColumn.querySelector(
          ".playground-empty-state",
        );
        if (visibleSections === 0) {
          if (!existingEmptyMsg) {
            const emptyMsg = document.createElement("div");
            emptyMsg.className = "playground-empty-state";
            emptyMsg.dataset.hiddenBySync = "true";
            emptyMsg.innerHTML = `
              <div class="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Nenhum parâmetro necessário
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                Esta rota não possui parâmetros editáveis. Clique em <b>Try it</b> para testar a resposta. 🚀
              </div>
            `;
            const container = paramColumn.querySelector(".space-y-2.mt-6");
            if (container) container.appendChild(emptyMsg);
          }
        } else if (existingEmptyMsg) {
          existingEmptyMsg.remove();
        }
      }
    }
  };

  let _currentConfig = { url: "", key: "" };

  const syncCodeBlocks = () => {
    const apiKey = getCookie("api_key");
    const rawUrl = getCookie("api_url") || "";
    const apiDomain = rawUrl.replace(/https?:\/\//, "").replace(/\/$/, "");
    const apiBase = rawUrl.replace(/\/$/, "");

    // Detect config change and reset cache if needed
    if (apiKey !== _currentConfig.key || rawUrl !== _currentConfig.url) {
      _currentConfig = { url: rawUrl, key: apiKey };
      // Force re-sync of everything
      document.querySelectorAll("[data-synced]").forEach((el) => {
        delete el.dataset.synced;
      });
    }

    if (!apiKey && !apiDomain) {
      // Mark all code blocks as synced even without cookies so they stay visible
      document
        .querySelectorAll(
          "pre:not([data-synced]), code:not([data-synced]), .shiki:not([data-synced])",
        )
        .forEach((el) => {
          el.dataset.synced = "true";
        });
      return;
    }

    // Aggressive selector: Catch anything that might contain the placeholder
    // We target only elements that haven't been synced yet to be efficient
    const elements = document.querySelectorAll(
      "pre:not([data-synced]), code:not([data-synced]), .shiki:not([data-synced]), .code-block:not([data-synced]), [class*='Code']:not([data-synced]), [class*='playground']:not([data-synced]), .method-pills:not([data-synced]), .text-sm.font-mono:not([data-synced])",
    );

    elements.forEach((block) => {
      const html = block.innerHTML;
      if (!html) return;

      // Skip actual input fields to avoid breaking user typing
      if (block.tagName === "INPUT" || block.tagName === "TEXTAREA") return;

      let newHtml = html;
      let changed = false;

      // Replace domain with flexible regex for optional spaces (Mintlify artifact)
      if (apiDomain) {
        // Handle https://api.example.com and variants
        const domainRegex =
          /https?:\/\/(api\.)?example\.com(\s+)?|api\.example\.com|example\.com/g;
        if (domainRegex.test(newHtml)) {
          newHtml = newHtml.replace(domainRegex, (match) => {
            if (match.startsWith("http")) {
              return apiBase + (match.includes(" ") ? " " : "");
            }
            return apiDomain;
          });
          changed = true;
        }
      }

      // Replace API key
      if (apiKey) {
        const keyPatterns = [
          /xxxxxxxxxx/g,
          /SUA_SENHA_SECRETA/g,
          /&lt;x-api-key&gt;/g,
        ];
        keyPatterns.forEach((pattern) => {
          if (pattern.test(newHtml)) {
            newHtml = newHtml.replace(pattern, apiKey);
            changed = true;
          }
        });
      }

      // Mark as synced BEFORE updating HTML to prevent loop/flicker
      block.dataset.synced = "true";

      if (changed && newHtml !== html) {
        block.innerHTML = newHtml;
      }
    });

    // Also run text replacement for non-code elements
    replaceApiTextInDOM();
  };

  // --- Dedicated observer for code blocks (catches React re-renders instantly) ---
  let _codeBlockDebounce = null;
  const startCodeBlockObserver = () => {
    const sideLayout = document.getElementById("content-side-layout");
    if (!sideLayout || sideLayout.dataset.codeObserver) return;
    sideLayout.dataset.codeObserver = "true";

    new MutationObserver(() => {
      // Smallest possible debounce to catch render frame
      clearTimeout(_codeBlockDebounce);
      _codeBlockDebounce = setTimeout(syncCodeBlocks, 0);
    }).observe(sideLayout, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  };

  // Replace text in elements (useful for playground base URL display)
  const replaceApiTextInDOM = () => {
    const apiBase = getCookie("api_url")?.replace(/\/$/, "");
    const apiKey = getCookie("api_key");
    if (!apiBase) return;

    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null,
      false,
    );

    let node;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      if (!parent) continue;

      // Skip inputs/textareas to avoid breaking user typing
      const isInput =
        parent.tagName === "INPUT" ||
        parent.tagName === "TEXTAREA" ||
        parent.closest(".api-playground-input") ||
        parent.getAttribute("contenteditable") === "true";
      if (isInput) {
        continue;
      }

      const text = node.textContent;
      if (
        text.includes("example.com") ||
        text.includes("xxxxxxxxxx") ||
        text.includes("SUA_SENHA_SECRETA")
      ) {
        let newText = text;

        // Handle URL with optional trailing space before slash
        newText = newText.replace(
          /https?:\/\/(api\.)?example\.com(\s+)?/g,
          (match) => {
            return apiBase + (match.includes(" ") ? " " : "");
          },
        );
        newText = newText.replace(
          /api\.example\.com|example\.com/g,
          apiBase.replace(/https?:\/\//, ""),
        );

        if (apiKey) {
          newText = newText.replace(/xxxxxxxxxx|SUA_SENHA_SECRETA/g, apiKey);
        }

        if (newText !== text) {
          node.textContent = newText;
        }
      }
    }
  };

  // Initialize configuration if we are on the config page
  let _configLoaded = false;
  function initConfigPage() {
    if (document.getElementById("api_url")) {
      // Attach focus/blur listeners once to prevent overwrite during typing
      ["api_url", "api_key", "internal_secret"].forEach((id) => {
        const el = document.getElementById(id);
        if (el && !el.dataset.configGuard) {
          el.addEventListener("focus", () => {
            _configEditing = true;
          });
          el.addEventListener("blur", () => {
            _configEditing = false;
          });
          el.dataset.configGuard = "true";
        }
      });

      // Only load cookie values on FIRST visit to the config page
      if (!_configLoaded) {
        loadConfigSettings();
        _configLoaded = true;
      }
      setupConfigListeners();
    } else {
      // If we left the config page, allow reload on next visit
      _configLoaded = false;
    }
    syncPlaygroundUI();
    syncCodeBlocks();
  }

  // --- Main Initializers ---

  hijackCodeBlockCopy();
  renameTryItButton();
  translateUI();
  toggleBodyScroll();
  initConfigPage();
  startCodeBlockObserver();

  let isUpdating = false;
  const runUpdates = () => {
    if (isUpdating) return;
    isUpdating = true;

    renameTryItButton();
    translateUI();
    colorRailwayDomain();
    hijackCodeBlockCopy();
    initConfigPage();
    replaceApiTextInDOM();
    startCodeBlockObserver();
    hideBaseUrl();
    cleanOrphanAuthInputs();

    setTimeout(() => {
      isUpdating = false;
    }, 100);
  };

  [50, 200, 500, 1000, 2000].forEach((delay) => {
    setTimeout(runUpdates, delay);
  });

  // --- Hybrid Intelligence Engine ---

  let _burstActive = false;
  let _burstTimer = null;
  let _burstInterval = null;

  const triggerBurst = () => {
    if (_burstActive) {
      // Refresh the 3-second timer if already active
      clearTimeout(_burstTimer);
      _burstTimer = setTimeout(stopBurst, 3000);
      return;
    }

    _burstActive = true;
    // Heavy lifting for 3 seconds (very fast to catch React)
    _burstInterval = setInterval(() => {
      syncCodeBlocks();
      syncPlaygroundUI();
      translateUI();
      renameTryItButton();
      hideBaseUrl();
      cleanOrphanAuthInputs();
    }, 150);

    _burstTimer = setTimeout(stopBurst, 3000);
  };

  const stopBurst = () => {
    _burstActive = false;
    clearInterval(_burstInterval);
    _burstInterval = null;
  };

  // 1. Initial burst on load
  triggerBurst();

  // 2. Observer-based triggers
  const observer = new MutationObserver((mutations) => {
    const isInternal = mutations.some(
      (m) =>
        (m.target.dataset &&
          (m.target.dataset.synced || m.target.dataset.hiddenBySync)) ||
        (m.type === "attributes" &&
          (m.attributeName === "style" ||
            (m.attributeName && m.attributeName.startsWith("data-")))),
    );

    if (!isInternal) {
      runUpdates();
      // If we see structural changes (like a modal opening), trigger a burst
      const isStructural = mutations.some(
        (m) =>
          m.type === "childList" ||
          m.target.classList?.contains("api-playground-modal"),
      );
      if (isStructural) triggerBurst();
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    characterData: true,
  });

  // 3. User Interaction Triggers
  document.addEventListener("click", triggerBurst, {
    capture: true,
    passive: true,
  });
  document.addEventListener("mousedown", triggerBurst, {
    capture: true,
    passive: true,
  });

  // Handle URL changes
  let lastUrl = window.location.href;
  new MutationObserver(() => {
    const currentUrl = window.location.href;
    if (currentUrl !== lastUrl) {
      lastUrl = currentUrl;
      triggerBurst(); // Instant burst on navigation
      setTimeout(runUpdates, 100);
    }
  }).observe(document.querySelector("title") || document.head, {
    childList: true,
    subtree: true,
  });

  // Inject No-Flicker CSS (only when cookies are configured)
  const _hasCookiesForFlicker = getCookie("api_url") && getCookie("api_key");
  if (
    _hasCookiesForFlicker &&
    !document.getElementById("zap-unlocked-no-flicker")
  ) {
    const flickerStyle = document.createElement("style");
    flickerStyle.id = "zap-unlocked-no-flicker";
    flickerStyle.textContent = `
    /* 1. Prevent flickering by hiding text blocks until synced */
    [class*="playground"] code:not([data-synced]),
    [class*="Code"] pre:not([data-synced]),
    .shiki:not([data-synced]),
    .api-playground pre:not([data-synced]) {
      visibility: hidden !important;
    }

    /* 2. INSTANT REMOVE for auth sections */
    .space-y-2.mt-6 > div:has(input[placeholder*="x-api-key"]),
    .space-y-2.mt-6 > div:has(input[id*="x-api-key"]),
    .space-y-2.mt-6 > div:has(input[placeholder*="SUA_SENHA_SECRETA"]),
    .space-y-2.mt-6 > div:has(div[title="x-api-key"]),
    .api-playground-param:has(input[id*="x-api-key"]),
    .api-playground-param:has(input[placeholder*="x-api-key"]),
    [class*="ParamField"]:has(input[id*="x-api-key"]),
    [class*="ParamField"]:has(input[placeholder*="x-api-key"]),
    .flex.flex-row.gap-4:has(input[placeholder*="SUA_SENHA_SECRETA"]) {
      display: none !important;
    }
  `;
    document.head.appendChild(flickerStyle);
  }

  // Hide copy buttons on quickstart page
  if (window.location.pathname.includes("/essentials/quickstart")) {
    const qsStyle = document.createElement("style");
    qsStyle.textContent = `
      [data-testid="copy-code-button"] {
        display: none !important;
      }
      [data-fade-overlay="true"] {
        display: none !important;
      }
    `;
    document.head.appendChild(qsStyle);
  }
})();
