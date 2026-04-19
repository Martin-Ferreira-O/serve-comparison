# serve-comparison

`serve-comparison` es una app FastAPI que recibe snapshots de cursos y evaluaciones por participante, los guarda en PostgreSQL y expone un dashboard para comparar rendimiento entre personas, cursos, semestres y evaluaciones.

## Que hace el proyecto

- Expone un dashboard HTML en `/`.
- Expone datos del dashboard en `/api/comparison/dashboard`.
- Recibe sincronizaciones de datos en `/api/comparison/sync`.
- Permite que cada participante reclame su identidad una sola vez usando un nombre visible preasignado y una pass.
- Despues del claim inicial, cada participante sigue sincronizando con su `sync_token`.

## Modelo de datos

- `participants`: identidades reclamadas y su `sync_token` hasheado.
- `claim_invites`: invitaciones pendientes o ya usadas para el primer claim.
- `courses`, `participant_course_attempts`, `participant_assessments`: snapshot academico visible en el dashboard.
- `sync_runs`: historial basico de sincronizaciones.

## Flujo de claim y sync

1. Un operador crea una invitacion para un participante con su nombre visible exacto.
2. El participante hace su primera sincronizacion enviando `participant_name` y `claim_code`.
3. La API valida la invitacion, marca el claim como usado y devuelve un `sync_token`.
4. Las siguientes sincronizaciones usan `participant_name` + `sync_token`.

## Requisitos

- Python 3.12+
- Una base PostgreSQL accesible desde la app

## Variables de entorno

- `DATABASE_URL`: cadena de conexion PostgreSQL.
- `PORT`: puerto local, opcional. Por defecto `8000`.

Ejemplo:

```bash
export DATABASE_URL='postgresql://user:password@host/dbname?sslmode=require'
export PORT=8000
```

## Desarrollo local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:create_app --factory --reload
```

## Agregar un participante

Las invitaciones ya no viven en un archivo JSON. Se guardan directamente en PostgreSQL.

Para crear o reemplazar la pass de una invitacion pendiente:

```bash
python -m app.scripts.invites add "Martin A."
```

Salida esperada:

```text
Participant: Martin A.
Pass: <generated-pass>
```

Notas:

- El script carga `.env` automaticamente antes de leer `DATABASE_URL`.
- La pass se genera automaticamente y se muestra una sola vez.
- Si el participante todavia no ha reclamado su identidad, el comando reemplaza la pass anterior.
- Si la identidad ya fue reclamada, el comando falla y no sobrescribe el registro.

## Ejecutar tests

Con `DATABASE_URL` configurado:

```bash
pytest
```

Los tests que dependen de PostgreSQL se omiten automaticamente si `DATABASE_URL` no existe.

## Deploy en Vercel

```bash
vercel
vercel --prod
```

Notas operativas:

- Vercel usa filesystem efimero, asi que los datos persistentes deben vivir en PostgreSQL.
- Esta version ya no depende de archivos locales para las invitaciones.
- Antes de que alguien sincronice por primera vez, crea su invitacion con `python -m app.scripts.invites add "Nombre"` o mediante una conexion directa a la misma base.
