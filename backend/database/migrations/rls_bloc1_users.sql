-- =====================================================
-- RLS ÉTAPE PAR ÉTAPE
-- Exécutez chaque bloc séparément
-- =====================================================

-- BLOC 1: Activer RLS sur users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_select" ON users;
CREATE POLICY "users_select" ON users FOR SELECT USING (auth.uid()::text = id::text);

DROP POLICY IF EXISTS "users_update" ON users;
CREATE POLICY "users_update" ON users FOR UPDATE USING (auth.uid()::text = id::text);

DROP POLICY IF EXISTS "users_insert" ON users;
CREATE POLICY "users_insert" ON users FOR INSERT WITH CHECK (auth.uid()::text = id::text);

SELECT 'Users RLS OK' as status;
