import { mockData } from "../services/mockData.js";
import { translate } from "../i18n/index.js";
import { icon } from "../components/icons.js";
import { API_BASE_URL } from "../config.js";
import { state as appState } from "../state.js";

const FARMER_NAME_KEY = "agriguide.farmerName";
const MEDIA_TYPES = new Map([
  [".jpg", "image"],
  [".jpeg", "image"],
  [".png", "image"],
  [".webp", "image"],
  [".gif", "image"],
  [".mp4", "video"],
  [".webm", "video"],
]);
const MAX_IMAGE_BYTES = 8 * 1024 * 1024;
const MAX_VIDEO_BYTES = 60 * 1024 * 1024;

const communityState = {
  loading: true,
  posts: [],
  category: "all",
  tab: "profile",
  profileFilter: "all",
  selectedId: null,
  detail: null,
  detailLoading: false,
  composerOpen: false,
  farmerName: "",
  upload: null,
  lightboxId: null,
  message: "",
  error: "",
};

try {
  communityState.farmerName = localStorage.getItem(FARMER_NAME_KEY) ?? "";
} catch {
  // Storage may be disabled; the app still works without a remembered name.
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function t(language, key, values = {}) {
  let text = translate(language, key);
  for (const [name, value] of Object.entries(values)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }
  return text;
}

function clearUpload() {
  if (communityState.upload?.url) URL.revokeObjectURL(communityState.upload.url);
  communityState.upload = null;
}

function setStatus(language, text, isError = false) {
  communityState.message = isError ? "" : text;
  communityState.error = isError ? text : "";
  const status = document.querySelector("#community-status");
  if (status) {
    status.textContent = text;
    status.className = isError ? "error-message" : "success-message";
  }
}

function replyCountLabel(language, count) {
  return t(language, count === 1 ? "replyCountOne" : "replyCount", { count });
}

function categoryLabel(language, value) {
  const match = mockData.communityCategories.find((item) => item.value === value);
  return match ? t(language, match.key) : escapeHtml(value);
}

function formatDate(iso) {
  return iso ? String(iso).slice(0, 10) : "";
}

function badge(text, className) {
  return `<span class="community-badge ${className}">${escapeHtml(text)}</span>`;
}

function mediaKind(name) {
  const value = String(name ?? "");
  const dot = value.lastIndexOf(".");
  return dot === -1 ? "" : (MEDIA_TYPES.get(value.slice(dot).toLowerCase()) ?? "");
}

function mediaElement(media, className, extra = "") {
  if (!media) return "";
  const src = escapeHtml(media.path);
  if (media.kind === "video") {
    return `<video class="${className}" src="${src}" ${extra}></video>`;
  }
  return `<img class="${className}" src="${src}" alt="" ${extra} />`;
}

function renderTabs(language) {
  return `
    <div class="community-tabs" role="tablist" aria-label="${escapeHtml(t(language, "communityTitle"))}">
      <button type="button" class="community-tab${communityState.tab === "profile" ? " is-active" : ""}"
        data-community-tab="profile" role="tab" aria-selected="${communityState.tab === "profile"}">
        ${icon("users")} ${t(language, "communityTabProfile")}
      </button>
      <button type="button" class="community-tab${communityState.tab === "questions" ? " is-active" : ""}"
        data-community-tab="questions" role="tab" aria-selected="${communityState.tab === "questions"}">
        ${icon("edit")} ${t(language, "communityTabQuestions")}
      </button>
    </div>
  `;
}

function renderProfile(language) {
  const posts = communityState.posts;
  const mediaPosts = posts.filter((post) => post.media);
  const feedPosts =
    communityState.profileFilter === "mine"
      ? mediaPosts.filter((post) => post.author === communityState.farmerName)
      : mediaPosts;
  const myCount = communityState.farmerName
    ? posts.filter((post) => post.author === communityState.farmerName).length
    : 0;
  const initial = escapeHtml((communityState.farmerName || "F").trim().charAt(0).toUpperCase());

  const tiles = feedPosts.length
    ? feedPosts.map((post) => renderFeedTile(language, post)).join("")
    : `<p class="weather-status">${t(language, "communityNoMedia")}</p>`;

  return `
    <section class="profile-header">
      <div class="profile-avatar" aria-hidden="true">${initial}</div>
      <div class="profile-identity">
        <strong>${escapeHtml(communityState.farmerName || "Farmer")}</strong>
        <p class="report-note">${t(language, "communityProfileIntro")}</p>
      </div>
      <div class="profile-stats">
        <div class="profile-stat"><strong>${myCount}</strong><span>${t(language, "communityMyPosts")}</span></div>
        <div class="profile-stat"><strong>${posts.length}</strong><span>${t(language, "communityAllPosts")}</span></div>
      </div>
    </section>
    <div class="community-toolbar">
      <button type="button" id="ask-button" class="primary-button">${icon("edit")} ${t(language, "communityNewPost")}</button>
    </div>
    <div class="community-chips">
      <button type="button" class="chip${communityState.profileFilter === "all" ? " is-selected" : ""}"
        data-profile-filter="all">${t(language, "communityAllPosts")}</button>
      <button type="button" class="chip${communityState.profileFilter === "mine" ? " is-selected" : ""}"
        data-profile-filter="mine">${t(language, "communityMyPosts")}</button>
    </div>
    <div class="community-feed">${tiles}</div>
    <p class="report-note">${t(language, "communityMediaNote")}</p>
  `;
}

function renderFeedTile(language, post) {
  const media = post.media;
  const kindBadge = `<span class="tile-kind">${t(language, media.kind === "video" ? "communityVideo" : "communityPhoto")}</span>`;
  return `
    <button type="button" class="feed-tile" data-media-post="${escapeHtml(post.id)}"
      aria-label="${escapeHtml(post.title)}">
      ${mediaElement(media, "tile-media", 'loading="lazy" muted preload="metadata"')}
      ${kindBadge}
      <span class="tile-caption">${escapeHtml(post.title)}</span>
    </button>
  `;
}

function renderLightbox(language) {
  if (!communityState.lightboxId) return "";
  const post = communityState.posts.find((item) => item.id === communityState.lightboxId);
  if (!post?.media) return "";

  return `
    <div class="media-lightbox" data-lightbox-overlay>
      <div class="media-lightbox-card" role="dialog" aria-modal="true" aria-label="${escapeHtml(post.title)}">
        <div class="lightbox-head">
          <strong>${escapeHtml(post.author)}</strong>
          <button type="button" class="lightbox-close" data-close-lightbox aria-label="${t(language, "cancel")}">✕</button>
        </div>
        ${mediaElement(post.media, "lightbox-media", post.media.kind === "video" ? 'controls autoplay' : "")}
        <div class="lightbox-body">
          <p class="lightbox-caption">${escapeHtml(post.title)}</p>
          <p class="lightbox-details">${escapeHtml(post.body)}</p>
          <div class="post-meta">
            <span>${formatDate(post.created_at)}</span>
            <span>${replyCountLabel(language, post.reply_count)}</span>
            <button type="button" class="report-button" data-report-post="${escapeHtml(post.id)}">${t(language, "report")}</button>
          </div>
          <button type="button" class="secondary-button" data-discuss="${escapeHtml(post.id)}">
            ${t(language, "communityOpenDiscussion")}
          </button>
        </div>
      </div>
    </div>
  `;
}

function renderComposer(language) {
  const categories = mockData.communityCategories
    .map((item) => `<option value="${item.value}">${t(language, item.key)}</option>`)
    .join("");
  const languages = mockData.languages
    .map(
      (item) =>
        `<option value="${item.code}"${item.code === appState.language ? " selected" : ""}>${escapeHtml(item.label)}</option>`,
    )
    .join("");
  const upload = communityState.upload;
  const preview = upload
    ? `<div class="media-preview-wrap">
         ${mediaElement({ path: upload.url, kind: upload.kind }, "media-preview", "")}
         <p class="report-note">${t(language, "communityMediaAttached", { name: upload.name })}</p>
         <button type="button" id="remove-media" class="secondary-button">${t(language, "communityRemoveMedia")}</button>
       </div>`
    : "";
  const submitLabel = communityState.tab === "profile" ? "communityNewPost" : "publish";

  return `
    <section class="composer-card">
      <form id="post-form" class="profile-form">
        <div class="form-grid">
          <div>
            <label class="field-label" for="community-name">${t(language, "fieldName")}</label>
            <input id="community-name" class="field-input" type="text" maxlength="60"
              value="${escapeHtml(communityState.farmerName)}" placeholder="${t(language, "namePlaceholder")}" />
          </div>
          <div>
            <label class="field-label" for="community-category">${t(language, "fieldCategory")}</label>
            <select id="community-category" class="field-input">${categories}</select>
          </div>
          <div>
            <label class="field-label" for="community-language">${t(language, "fieldLanguage")}</label>
            <select id="community-language" class="field-input">${languages}</select>
          </div>
        </div>
        <label class="field-label" for="community-title">${t(language, "communityCaption")}</label>
        <input id="community-title" class="field-input" type="text" minlength="3" maxlength="140"
          placeholder="${t(language, "communityCaptionPlaceholder")}" required />
        <label class="field-label" for="community-body">${t(language, "fieldBody")}</label>
        <textarea id="community-body" class="field-input" rows="3" maxlength="2000"
          placeholder="${t(language, "bodyPlaceholder")}" required></textarea>
        <label class="field-label" for="community-media">${t(language, "communityMediaOptional")}</label>
        <div class="media-dropzone">
          <input id="community-media" class="field-input" type="file"
            accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm" />
          <p class="report-note">${t(language, "communityMediaTypeError")}</p>
        </div>
        ${preview}
        <div class="form-actions">
          <button type="submit" class="primary-button">${icon("check")} ${t(language, submitLabel)}</button>
          <button type="button" id="cancel-post" class="secondary-button">${t(language, "cancel")}</button>
        </div>
      </form>
    </section>
  `;
}

function renderQuestionsList(language) {
  const chips = [
    `<button type="button" class="chip${communityState.category === "all" ? " is-selected" : ""}" data-category="all">${t(language, "allCategories")}</button>`,
    ...mockData.communityCategories.map(
      (item) =>
        `<button type="button" class="chip${communityState.category === item.value ? " is-selected" : ""}" data-category="${item.value}">${t(language, item.key)}</button>`,
    ),
  ].join("");

  const posts = communityState.posts.length
    ? communityState.posts.map((post) => renderPostCard(language, post)).join("")
    : `<p class="weather-status">${t(language, "noPosts")}</p>`;

  return `
    <div class="community-toolbar">
      <button type="button" id="ask-button" class="primary-button">${icon("edit")} ${t(language, "askQuestion")}</button>
    </div>
    <div class="community-chips">${chips}</div>
    <div class="community-list">${posts}</div>
    <p class="report-note">${t(language, "reportNote")}</p>
  `;
}

function renderPostCard(language, post) {
  const badges = [
    post.is_demo ? badge(t(language, "demoPost"), "demo") : "",
    post.media ? badge(t(language, post.media.kind === "video" ? "communityVideo" : "communityPhoto"), "category") : "",
    badge(categoryLabel(language, post.category), "category"),
    badge(escapeHtml(post.language.toUpperCase()), "language"),
  ].join("");

  return `
    <article class="community-post-card">
      <div class="community-badges">${badges}</div>
      <button type="button" class="community-post-open" data-post="${escapeHtml(post.id)}">
        <strong>${escapeHtml(post.title)}</strong>
        <span class="post-preview">${escapeHtml(post.body)}</span>
      </button>
      <div class="post-meta">
        <span>${escapeHtml(post.author)}</span>
        <span>${formatDate(post.created_at)}</span>
        <span>${replyCountLabel(language, post.reply_count)}</span>
        <button type="button" class="report-button" data-report-post="${escapeHtml(post.id)}">${t(language, "report")}</button>
      </div>
    </article>
  `;
}

function renderReply(language, reply) {
  const badges = [
    reply.is_demo ? badge(t(language, "demoReply"), "demo") : "",
    badge(escapeHtml(reply.language.toUpperCase()), "language"),
  ].join("");

  return `
    <article class="community-reply">
      <div class="community-badges">${badges}</div>
      <p>${escapeHtml(reply.body)}</p>
      <div class="post-meta">
        <span>${escapeHtml(reply.author)}</span>
        <span>${formatDate(reply.created_at)}</span>
        <button type="button" class="report-button" data-report-reply="${escapeHtml(reply.id)}">${t(language, "report")}</button>
      </div>
    </article>
  `;
}

function renderDetail(language) {
  if (communityState.detailLoading || !communityState.detail) {
    return `<p class="weather-status">${t(language, "weatherLoading")}</p>`;
  }

  const post = communityState.detail.post;
  const replies = communityState.detail.replies ?? [];
  const badges = [
    post.is_demo ? badge(t(language, "demoPost"), "demo") : "",
    post.media ? badge(t(language, post.media.kind === "video" ? "communityVideo" : "communityPhoto"), "category") : "",
    badge(categoryLabel(language, post.category), "category"),
    badge(escapeHtml(post.language.toUpperCase()), "language"),
  ].join("");

  return `
    <div class="community-detail">
      <button type="button" id="back-button" class="secondary-button">${t(language, "backToQuestions")}</button>
      <article class="community-post-card is-detail">
        <div class="community-badges">${badges}</div>
        ${post.media ? `<div class="detail-media">${mediaElement(post.media, "detail-media-item", post.media.kind === "video" ? "controls" : "")}</div>` : ""}
        <h3>${escapeHtml(post.title)}</h3>
        <p>${escapeHtml(post.body)}</p>
        <div class="post-meta">
          <span>${escapeHtml(post.author)}</span>
          <span>${formatDate(post.created_at)}</span>
          <button type="button" class="report-button" data-report-post="${escapeHtml(post.id)}">${t(language, "report")}</button>
        </div>
      </article>

      <section class="replies-section">
        <h3>${replyCountLabel(language, replies.length)}</h3>
        ${replies.length ? replies.map((reply) => renderReply(language, reply)).join("") : `<p class="weather-status">${t(language, "noReplies")}</p>`}
      </section>

      <section class="composer-card">
        <form id="reply-form" class="profile-form">
          <label class="field-label" for="reply-name">${t(language, "fieldName")}</label>
          <input id="reply-name" class="field-input" type="text" maxlength="60"
            value="${escapeHtml(communityState.farmerName)}" placeholder="${t(language, "namePlaceholder")}" />
          <label class="field-label" for="reply-body">${t(language, "fieldBody")}</label>
          <textarea id="reply-body" class="field-input" rows="3" maxlength="1000" placeholder="${t(language, "replyPlaceholder")}" required></textarea>
          <div class="form-actions">
            <button type="submit" class="primary-button">${icon("check")} ${t(language, "sendReply")}</button>
          </div>
        </form>
      </section>
      <p class="report-note">${t(language, "reportNote")}</p>
    </div>
  `;
}

function renderView(language) {
  if (communityState.selectedId) return renderDetail(language);

  const content = communityState.composerOpen
    ? renderComposer(language)
    : communityState.tab === "profile"
      ? renderProfile(language)
      : renderQuestionsList(language);

  return `${renderTabs(language)}${content}${renderLightbox(language)}`;
}

function updateView(language) {
  const target = document.querySelector("#community-view");
  if (target) target.innerHTML = renderView(language);

  const status = document.querySelector("#community-status");
  if (status) {
    status.textContent = communityState.message || communityState.error;
    status.className = communityState.error ? "error-message" : "success-message";
  }
}

async function loadPosts(language, preserveStatus = false) {
  communityState.loading = true;
  if (!preserveStatus) setStatus(language, "");
  updateView(language);

  const params = new URLSearchParams();
  if (communityState.category !== "all") params.set("category", communityState.category);

  try {
    const response = await fetch(`${API_BASE_URL}/api/community/posts?${params.toString()}`);
    if (!response.ok) throw new Error("post load failed");
    communityState.posts = (await response.json()).posts ?? [];
    if (communityState.lightboxId && !communityState.posts.some((post) => post.id === communityState.lightboxId)) {
      communityState.lightboxId = null;
    }
  } catch {
    setStatus(language, t(language, "loadError"), true);
  } finally {
    communityState.loading = false;
    updateView(language);
  }
}

async function loadDetail(language, postId) {
  communityState.selectedId = postId;
  communityState.detail = null;
  communityState.detailLoading = true;
  setStatus(language, "");
  updateView(language);

  try {
    const response = await fetch(`${API_BASE_URL}/api/community/posts/${encodeURIComponent(postId)}`);
    if (!response.ok) throw new Error("detail load failed");
    communityState.detail = await response.json();
  } catch {
    setStatus(language, t(language, "loadError"), true);
  } finally {
    communityState.detailLoading = false;
    updateView(language);
  }
}

async function uploadSelectedFile(file, language, submitButton) {
  const form = new FormData();
  form.append("file", file, file.name);

  const response = await fetch(`${API_BASE_URL}/api/community/upload`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    const code = response.status;
    setStatus(
      language,
      t(
        language,
        code === 413 ? "communityMediaTooLarge" : code === 415 ? "communityMediaTypeError" : "communityUploadError",
      ),
      true,
    );
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.innerHTML = `${icon("check")} ${t(language, communityState.tab === "profile" ? "communityNewPost" : "publish")}`;
    }
    return null;
  }
  return response.json();
}

async function createPost(language) {
  const value = (selector) => document.querySelector(selector)?.value ?? "";
  const author = value("#community-name").trim();
  const payload = {
    author,
    category: value("#community-category"),
    language: value("#community-language"),
    title: value("#community-title"),
    body: value("#community-body"),
  };

  if (author) {
    communityState.farmerName = author;
    try {
      localStorage.setItem(FARMER_NAME_KEY, author);
    } catch {
      // A blocked storage API must not stop posting.
    }
  }

  const submitButton = document.querySelector('#post-form button[type="submit"]');
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.textContent = t(language, "communityUploading");
  }

  try {
    let mediaMeta = null;
    if (communityState.upload?.file) {
      mediaMeta = await uploadSelectedFile(communityState.upload.file, language, submitButton);
      if (!mediaMeta) return;
    }

    const response = await fetch(`${API_BASE_URL}/api/community/posts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...payload,
        media_path: mediaMeta?.path ?? "",
        media_kind: mediaMeta?.kind ?? "",
        media_name: mediaMeta?.name ?? "",
      }),
    });
    if (!response.ok) throw new Error("post create failed");

    clearUpload();
    communityState.composerOpen = false;
    communityState.category = "all";
    setStatus(language, t(language, "postCreated"));
    await loadPosts(language, true);
  } catch {
    setStatus(language, t(language, "createError"), true);
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.innerHTML = `${icon("check")} ${t(language, communityState.tab === "profile" ? "communityNewPost" : "publish")}`;
    }
  }
}

async function createReply(language, postId) {
  const value = (selector) => document.querySelector(selector)?.value ?? "";
  const author = value("#reply-name").trim();
  if (author) {
    communityState.farmerName = author;
    try {
      localStorage.setItem(FARMER_NAME_KEY, author);
    } catch {
      // Ignore blocked storage.
    }
  }

  const payload = {
    author,
    language: communityState.detail?.post?.language ?? appState.language,
    body: value("#reply-body"),
  };

  try {
    const response = await fetch(`${API_BASE_URL}/api/community/posts/${encodeURIComponent(postId)}/replies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("reply create failed");

    setStatus(language, t(language, "replyCreated"));
    const detail = await fetch(`${API_BASE_URL}/api/community/posts/${encodeURIComponent(postId)}`);
    communityState.detail = await detail.json();
    updateView(language);
  } catch {
    setStatus(language, t(language, "createError"), true);
  }
}

async function report(kind, id, language) {
  const path = kind === "post" ? `posts/${encodeURIComponent(id)}/report` : `replies/${encodeURIComponent(id)}/report`;
  try {
    const response = await fetch(`${API_BASE_URL}/api/community/${path}`, { method: "POST" });
    if (!response.ok) throw new Error("report failed");
    setStatus(language, t(language, "reported"));
  } catch {
    setStatus(language, t(language, "createError"), true);
  }
}

function selectMedia(file, language, input) {
  const kind = mediaKind(file.name);
  if (!kind) {
    input.value = "";
    setStatus(language, t(language, "communityMediaTypeError"), true);
    return;
  }
  if (file.size > (kind === "video" ? MAX_VIDEO_BYTES : MAX_IMAGE_BYTES)) {
    input.value = "";
    setStatus(language, t(language, "communityMediaTooLarge"), true);
    return;
  }
  if (communityState.upload?.url) URL.revokeObjectURL(communityState.upload.url);
  communityState.upload = {
    file,
    url: URL.createObjectURL(file),
    kind,
    name: file.name,
  };
  setStatus(language, t(language, "communityMediaAttached", { name: file.name }));
  updateView(language);
}

function attachEvents(language) {
  const root = document.querySelector("#community-root");
  if (!root) return;

  root.addEventListener("click", (event) => {
    const tab = event.target.closest("[data-community-tab]");
    if (tab) {
      communityState.tab = tab.dataset.communityTab;
      communityState.selectedId = null;
      communityState.composerOpen = false;
      communityState.lightboxId = null;
      clearUpload();
      setStatus(language, "");
      updateView(language);
      return;
    }

    const filter = event.target.closest("[data-profile-filter]");
    if (filter) {
      communityState.profileFilter = filter.dataset.profileFilter;
      updateView(language);
      return;
    }

    if (event.target.closest("#ask-button")) {
      communityState.composerOpen = true;
      setStatus(language, "");
      updateView(language);
      return;
    }

    if (event.target.closest("#cancel-post")) {
      communityState.composerOpen = false;
      clearUpload();
      updateView(language);
      return;
    }

    if (event.target.closest("#remove-media")) {
      clearUpload();
      setStatus(language, "");
      updateView(language);
      return;
    }

    const mediaPost = event.target.closest("[data-media-post]");
    if (mediaPost) {
      communityState.lightboxId = mediaPost.dataset.mediaPost;
      updateView(language);
      return;
    }

    if (event.target.closest("[data-close-lightbox]") || event.target.matches("[data-lightbox-overlay]")) {
      communityState.lightboxId = null;
      updateView(language);
      return;
    }

    const discuss = event.target.closest("[data-discuss]");
    if (discuss) {
      communityState.lightboxId = null;
      communityState.tab = "questions";
      loadDetail(language, discuss.dataset.discuss);
      return;
    }

    const category = event.target.closest("[data-category]");
    if (category) {
      communityState.category = category.dataset.category;
      communityState.selectedId = null;
      loadPosts(language);
      return;
    }

    if (event.target.closest("#back-button")) {
      communityState.selectedId = null;
      communityState.composerOpen = false;
      updateView(language);
      return;
    }

    const openPost = event.target.closest("[data-post]");
    if (openPost) {
      loadDetail(language, openPost.dataset.post);
      return;
    }

    const reportPost = event.target.closest("[data-report-post]");
    if (reportPost) {
      report("post", reportPost.dataset.reportPost, language);
      return;
    }

    const reportReply = event.target.closest("[data-report-reply]");
    if (reportReply) {
      report("reply", reportReply.dataset.reportReply, language);
    }
  });

  root.addEventListener("change", (event) => {
    if (event.target.id === "community-media") {
      const file = event.target.files?.[0];
      if (file) selectMedia(file, language, event.target);
    }
  });

  root.addEventListener("submit", (event) => {
    if (event.target.id === "post-form") {
      event.preventDefault();
      createPost(language);
    } else if (event.target.id === "reply-form") {
      event.preventDefault();
      createReply(language, communityState.selectedId);
    }
  });
}

export function renderCommunity(language) {
  return `
    <section class="community-page">
      <header class="dashboard-header">
        <div class="feature-icon tone-violet">${icon("users")}</div>
        <div>
          <h2>${t(language, "communityTitle")}</h2>
          <p>${t(language, "communityIntro")}</p>
        </div>
      </header>
      <p id="community-status" class="success-message" role="status"></p>
      <div id="community-root"><div id="community-view">${renderView(language)}</div></div>
    </section>
  `;
}

export function initCommunity(language) {
  attachEvents(language);
  loadPosts(language);
}
