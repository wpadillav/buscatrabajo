# Cómo contribuir a Buscatrabajo

¡Gracias por interesarte en mejorar Buscatrabajo! Este documento te explica cómo contribuir de forma ordenada.

---

## 🐛 Reportar errores

Si encontrás un error:

1. Verificá que no haya un issue abierto que ya lo reporte.
2. Abrí un nuevo issue con:
   - Título claro y descriptivo.
   - Descripción del problema.
   - Pasos para reproducirlo.
   - Qué esperabas que pase vs. qué pasó.
   - Tu sistema operativo y versión de Python.

---

## 💡 Sugerir mejoras

Podés proponer nuevas funcionalidades, portales o mejoras en la interfaz.

1. Abrí un issue con el prefijo `[Feature]` o `[Mejora]`.
2. Explicá el problema que resuelve tu idea.
3. Si es posible, describí cómo te imaginas la implementación.

---

## 🛠️ Enviar cambios con Pull Request

### 1. Hacé un fork

Andá a https://github.com/wpadillav/buscatrabajo y clickeá en **Fork**.

### 2. Cloná tu fork

```bash
git clone https://github.com/TU_USUARIO/buscatrabajo.git
cd buscatrabajo
```

### 3. Configurá el remoto original

```bash
git remote add upstream https://github.com/wpadillav/buscatrabajo.git
```

### 4. Creá una rama para tu cambio

```bash
git checkout -b feature/nombre-descriptivo
```

### 5. Hacé tus cambios

- Seguí el estilo de código existente.
- Agregá tests si es necesario.
- Actualizá la documentación si tu cambio lo requiere.

### 6. Ejecutá los tests localmente

```bash
python -m pytest tests/
python -m py_compile main.py core/*.py web/server.py scrapers/*.py
```

### 7. Commiteá y pusheá

```bash
git add .
git commit -m "Descripción clara del cambio"
git push origin feature/nombre-descriptivo
```

### 8. Abrí un Pull Request

Desde tu fork en GitHub, abrí un PR hacia `wpadillav/buscatrabajo:main`.

---

## ✅ Estándares de código

- Usá tipado estático cuando sea posible (`list[str]`, `dict[str, int]`).
- Documentá funciones públicas con docstrings.
- Mantené los nombres descriptivos en español, como el resto del proyecto.
- No commitees datos personales, tokens ni contraseñas.
- No subas la base de datos `*.db`, CSVs ni logs (`data/` ya está en `.gitignore`).

---

## 🧪 Tests

Antes de enviar un PR, asegurate de que los tests pasen:

```bash
python -m pytest tests/
```

Si agregás una funcionalidad nueva, considerá agregar un test en `tests/`.

---

## 📚 Documentación

Si tu cambio afecta el uso del proyecto, actualizá:

- `README.md` para cambios generales.
- `docs/` para guías de usuario, arquitectura o desarrollo.
- `config.yaml` si agregás nuevas opciones de configuración.

---

## 🙌 Código de conducta

- Sé respetuoso en issues y pull requests.
- Aceptá la crítica constructiva.
- Priorizá el beneficio colectivo del proyecto.

---

## 📜 Licencia

Al contribuir, aceptás que tu código se publique bajo la licencia **AGPL-3.0** del proyecto.

---

## 📎 Links útiles

- [Índice de documentación](docs/README.md)
- [Guía de desarrollo](docs/desarrollo.md)
- [Arquitectura](docs/arquitectura.md)
- [Licencia](LICENSE)
