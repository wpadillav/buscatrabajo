"""
Base de datos SQLite para almacenar y consultar ofertas de empleo.

Ver docs/arquitectura.md para entender el modelo de persistencia.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from core.models import OfertaEmpleo


DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "ofertas.db"


class Database:
    """Base de datos SQLite para almacenar ofertas de empleo."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conexion(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        with self._conexion() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ofertas (
                    id_unico TEXT PRIMARY KEY,
                    id_externo TEXT NOT NULL,
                    portal TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    empresa TEXT,
                    ubicacion TEXT,
                    url TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_publicacion TEXT,
                    salario TEXT,
                    modalidad TEXT,
                    puntos_relevancia INTEGER DEFAULT 0,
                    palabras_detectadas TEXT,
                    es_relevante INTEGER DEFAULT 0,
                    primera_vez TEXT NOT NULL,
                    ultima_vez TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_relevante ON ofertas(es_relevante)"
            )

    def guardar(self, oferta: OfertaEmpleo) -> bool:
        """
        Guarda o actualiza una oferta. Retorna True si es nueva.
        """
        id_unico = oferta.id_unico()
        ahora = datetime.now().isoformat()

        with self._conexion() as conn:
            existe = conn.execute(
                "SELECT 1 FROM ofertas WHERE id_unico = ?", (id_unico,)
            ).fetchone()

            if existe:
                conn.execute(
                    """
                    UPDATE ofertas SET
                        titulo = ?,
                        empresa = ?,
                        ubicacion = ?,
                        url = ?,
                        descripcion = ?,
                        fecha_publicacion = ?,
                        salario = ?,
                        modalidad = ?,
                        puntos_relevancia = ?,
                        palabras_detectadas = ?,
                        es_relevante = ?,
                        ultima_vez = ?
                    WHERE id_unico = ?
                    """,
                    (
                        oferta.titulo,
                        oferta.empresa,
                        oferta.ubicacion,
                        oferta.url,
                        oferta.descripcion,
                        oferta.fecha_publicacion.isoformat() if oferta.fecha_publicacion else None,
                        oferta.salario,
                        oferta.modalidad,
                        oferta.puntos_relevancia,
                        ",".join(oferta.palabras_detectadas),
                        1 if oferta.es_relevante else 0,
                        ahora,
                        id_unico,
                    ),
                )
                return False

            conn.execute(
                """
                INSERT INTO ofertas (
                    id_unico, id_externo, portal, titulo, empresa, ubicacion, url,
                    descripcion, fecha_publicacion, salario, modalidad,
                    puntos_relevancia, palabras_detectadas, es_relevante,
                    primera_vez, ultima_vez
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id_unico,
                    oferta.id_externo,
                    oferta.portal,
                    oferta.titulo,
                    oferta.empresa,
                    oferta.ubicacion,
                    oferta.url,
                    oferta.descripcion,
                    oferta.fecha_publicacion.isoformat() if oferta.fecha_publicacion else None,
                    oferta.salario,
                    oferta.modalidad,
                    oferta.puntos_relevancia,
                    ",".join(oferta.palabras_detectadas),
                    1 if oferta.es_relevante else 0,
                    ahora,
                    ahora,
                ),
            )
            return True

    def obtener_relevantes(self, portal: str | None = None, limite: int = 100):
        with self._conexion() as conn:
            sql = "SELECT * FROM ofertas WHERE es_relevante = 1"
            params = []
            if portal:
                sql += " AND portal = ?"
                params.append(portal)
            sql += " ORDER BY puntos_relevancia DESC, ultima_vez DESC LIMIT ?"
            params.append(limite)
            return conn.execute(sql, params).fetchall()

    def contar(self) -> dict:
        with self._conexion() as conn:
            total = conn.execute("SELECT COUNT(*) FROM ofertas").fetchone()[0]
            relevantes = conn.execute(
                "SELECT COUNT(*) FROM ofertas WHERE es_relevante = 1"
            ).fetchone()[0]
            return {"total": total, "relevantes": relevantes}

    def filtrar(
        self,
        portal: str | None = None,
        busqueda: str | None = None,
        solo_relevantes: bool = True,
        pagina: int = 1,
        por_pagina: int = 20,
    ) -> tuple[list[sqlite3.Row], int]:
        """Filtra ofertas con paginación. Retorna (filas, total)."""
        where = ["1=1"]
        params = []

        if solo_relevantes:
            where.append("es_relevante = 1")
        if portal:
            where.append("portal = ?")
            params.append(portal)
        if busqueda:
            where.append(
                "(LOWER(titulo) LIKE ? OR LOWER(descripcion) LIKE ? OR LOWER(empresa) LIKE ?)"
            )
            like = f"%{busqueda}%"
            params.extend([like, like, like])

        where_sql = " AND ".join(where)

        with self._conexion() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM ofertas WHERE {where_sql}", params
            ).fetchone()[0]

            offset = (pagina - 1) * por_pagina
            filas = conn.execute(
                f"""
                SELECT * FROM ofertas
                WHERE {where_sql}
                ORDER BY puntos_relevancia DESC, ultima_vez DESC
                LIMIT ? OFFSET ?
                """,
                params + [por_pagina, offset],
            ).fetchall()
            return filas, total

    def portales(self) -> list[str]:
        with self._conexion() as conn:
            rows = conn.execute(
                "SELECT DISTINCT portal FROM ofertas ORDER BY portal"
            ).fetchall()
            return [row["portal"] for row in rows]

    def obtener_por_id(self, id_unico: str) -> sqlite3.Row | None:
        with self._conexion() as conn:
            return conn.execute(
                "SELECT * FROM ofertas WHERE id_unico = ?", (id_unico,)
            ).fetchone()

    def eliminar_no_vistas(self, ids_vistos: set[str], portal: str | None = None) -> int:
        """
        Elimina ofertas que no aparecieron en la corrida actual.
        Si se especifica portal, solo elimina ofertas de ese portal.
        """
        if not ids_vistos:
            return 0

        with self._conexion() as conn:
            sql = "DELETE FROM ofertas WHERE id_unico NOT IN ({})".format(
                ",".join("?" * len(ids_vistos))
            )
            params = list(ids_vistos)
            if portal:
                sql += " AND portal = ?"
                params.append(portal)
            cursor = conn.execute(sql, params)
            return cursor.rowcount
