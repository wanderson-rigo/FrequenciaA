-- Crie a tabela `faltas` no banco Supabase (Postgres) antes de usar o upload.
-- Ajuste tipos conforme necessário.

CREATE TABLE IF NOT EXISTS faltas (
  id bigserial PRIMARY KEY,
  nome text,
  disciplina text,
  data text,
  aula integer,
  faltas integer,
  carga_horaria numeric,
  percentual_faltas text,
  situacao text
);
