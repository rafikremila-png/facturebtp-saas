-- =====================================================
-- PARTIE 4: INDEX ET FONCTIONS
-- Exécutez cette partie en dernier
-- =====================================================

-- INDEXES FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_settings_user_id ON settings(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_client_id ON quotes(client_id);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_quotes_share_token ON quotes(share_token);
CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_invoices_client_id ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_invoices_quote_id ON invoices(quote_id);
CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON invoices(payment_status);
CREATE INDEX IF NOT EXISTS idx_invoices_share_token ON invoices(share_token);
CREATE INDEX IF NOT EXISTS idx_share_links_token ON share_links(token);
CREATE INDEX IF NOT EXISTS idx_predefined_items_category ON predefined_items(category);
CREATE INDEX IF NOT EXISTS idx_counters_user_type_year ON counters(user_id, counter_type, year);

-- FUNCTION FOR AUTO-UPDATE TIMESTAMPS
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- TRIGGERS FOR UPDATED_AT
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_settings_updated_at ON settings;
CREATE TRIGGER update_settings_updated_at 
    BEFORE UPDATE ON settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER update_subscriptions_updated_at 
    BEFORE UPDATE ON subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at 
    BEFORE UPDATE ON clients 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_quotes_updated_at ON quotes;
CREATE TRIGGER update_quotes_updated_at 
    BEFORE UPDATE ON quotes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_invoices_updated_at ON invoices;
CREATE TRIGGER update_invoices_updated_at 
    BEFORE UPDATE ON invoices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- FUNCTION TO AUTO-CREATE USER PROFILE ON SIGNUP
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
    INSERT INTO public.users (id, email, role, subscription_plan, trial_status, trial_started_at, trial_ends_at, quote_limit, invoice_limit)
    VALUES (
        NEW.id,
        NEW.email,
        'user',
        'trial',
        'trial',
        NOW(),
        NOW() + INTERVAL '7 days',
        5,
        5
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- TRIGGER TO AUTO-CREATE USER PROFILE
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- FUNCTION TO GENERATE DOCUMENT NUMBERS
CREATE OR REPLACE FUNCTION generate_document_number(
    p_user_id UUID,
    p_type VARCHAR,
    p_prefix VARCHAR DEFAULT NULL
)
RETURNS VARCHAR AS $$
DECLARE
    v_year INTEGER;
    v_counter INTEGER;
    v_prefix VARCHAR;
    v_number VARCHAR;
BEGIN
    v_year := EXTRACT(YEAR FROM NOW());
    v_prefix := COALESCE(p_prefix, CASE p_type WHEN 'quote' THEN 'DEV' ELSE 'FAC' END);
    
    -- Get or create counter
    INSERT INTO counters (user_id, counter_type, year, current_value, prefix)
    VALUES (p_user_id, p_type, v_year, 1, v_prefix)
    ON CONFLICT (user_id, counter_type, year) 
    DO UPDATE SET current_value = counters.current_value + 1
    RETURNING current_value INTO v_counter;
    
    -- Format number
    v_number := v_prefix || '-' || v_year || '-' || LPAD(v_counter::TEXT, 4, '0');
    
    RETURN v_number;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

SELECT 'Partie 4 (Index & Fonctions) exécutée avec succès!' as status;
SELECT 'MIGRATION COMPLÈTE!' as final_status;
