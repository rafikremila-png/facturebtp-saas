-- BLOC 4: Activer RLS sur invoices
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "invoices_select" ON invoices;
CREATE POLICY "invoices_select" ON invoices FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "invoices_insert" ON invoices;
CREATE POLICY "invoices_insert" ON invoices FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "invoices_update" ON invoices;
CREATE POLICY "invoices_update" ON invoices FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "invoices_delete" ON invoices;
CREATE POLICY "invoices_delete" ON invoices FOR DELETE USING (auth.uid()::text = user_id::text);

SELECT 'Invoices RLS OK' as status;
