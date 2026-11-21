// Hash-based routing keeps everything in one static HTML file.
// Example: #/weather means "show the weather page".

export function currentRoute() {
  return window.location.hash || "#/";
}

export function startRouter(onRouteChange) {
  window.addEventListener("hashchange", () => onRouteChange(currentRoute()));
}
