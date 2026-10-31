// Interfaz del acortador: valida la URL, llama a la API con fetch() y muestra el enlace corto.
const API_URL = (window.API_URL || "").replace(/\/+$/, "");

const form = document.getElementById("form");
const inputUrl = document.getElementById("url");
const botonEnviar = document.getElementById("enviar");
const error = document.getElementById("error");
const resultado = document.getElementById("resultado");
const corto = document.getElementById("corto");
const abrir = document.getElementById("abrir");
const aviso = document.getElementById("aviso");

function mostrarError(mensaje) {
  error.textContent = mensaje;
  error.hidden = false;
  resultado.hidden = true;
}

function esUrlValida(texto) {
  try {
    const url = new URL(texto);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const original = inputUrl.value.trim();
  error.hidden = true;

  if (!esUrlValida(original)) {
    mostrarError("Escribe una URL válida que empiece con http:// o https://");
    return;
  }

  botonEnviar.disabled = true;
  botonEnviar.textContent = "Acortando…";
  const control = new AbortController();
  const limite = setTimeout(() => control.abort(), 10000);

  try {
    const respuesta = await fetch(`${API_URL}/shorten`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ original_url: original }),
      signal: control.signal,
    });
    const datos = await respuesta.json().catch(() => null);
    if (!respuesta.ok) {
      mostrarError(respuesta.status === 422 ? "La API rechazó la URL: revisa que sea válida" : `La API respondió con el código ${respuesta.status}`);
      return;
    }
    corto.value = datos.short_url;
    abrir.href = datos.short_url;
    aviso.textContent = `Código: ${datos.short_code}`;
    resultado.hidden = false;
  } catch {
    mostrarError(`No se pudo conectar con el backend en ${API_URL || "(falta API_URL en config.js)"}`);
  } finally {
    clearTimeout(limite);
    botonEnviar.disabled = false;
    botonEnviar.textContent = "Acortar";
  }
});

// navigator.clipboard solo existe en HTTPS; el sitio de S3 es HTTP, así que hay respaldo.
document.getElementById("copiar").addEventListener("click", async () => {
  let copiado = false;
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(corto.value);
      copiado = true;
    } catch {
      copiado = false;
    }
  }
  if (!copiado) {
    corto.select();
    copiado = document.execCommand("copy");
  }
  aviso.textContent = copiado ? "Enlace copiado" : "Selecciona el enlace y copia con Ctrl+C";
});
