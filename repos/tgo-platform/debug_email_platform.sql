-- Debug script to check email platform configuration
-- Run this to see the platform config for the failing platform

SELECT 
    id,
    name,
    type,
    is_active,
    config->>'imap_host' as imap_host,
    config->>'imap_port' as imap_port,
    config->>'imap_username' as imap_username,
    config->>'imap_use_ssl' as imap_use_ssl,
    config->>'mailbox' as mailbox,
    config->>'smtp_host' as smtp_host,
    config->>'smtp_port' as smtp_port,
    config->>'smtp_username' as smtp_username,
    created_at
FROM pt_platforms
WHERE id = '722d5971-af62-4f48-ae32-286cc60dfb7e'::uuid;

-- Also check all active email platforms
SELECT 
    id,
    name,
    config->>'imap_host' as imap_host,
    config->>'mailbox' as mailbox,
    is_active
FROM pt_platforms
WHERE type = 'email' 
  AND is_active = true 
  AND deleted_at IS NULL
ORDER BY created_at DESC;

