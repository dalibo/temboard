-- Repository upgrade script from 2.2 to 3.0
CREATE OR REPLACE FUNCTION monitoring.insert_instance_availability(i_tstz TIMESTAMP WITH TIME ZONE, i_instance_id INTEGER, i_available BOOLEAN)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
  s_available BOOLEAN;
BEGIN
  SELECT available::BOOLEAN FROM monitoring.instance_availability
  WHERE instance_id = i_instance_id
  ORDER BY datetime desc LIMIT 1 INTO s_available;
  IF s_available IS NULL OR i_available <> s_available THEN
    INSERT INTO monitoring.instance_availability (datetime, instance_id, available)
    VALUES (i_tstz, i_instance_id, i_available);
  END IF;
END;
$$;

CREATE TABLE monitoring.instance_availability(datetime TIMESTAMP WITH TIME ZONE NOT NULL, instance_id INTEGER NOT NULL, available BOOLEAN NOT NULL);
CREATE INDEX idx_instance_availability ON monitoring.instance_availability (instance_id, datetime);

GRANT ALL ON TABLE monitoring.instance_availability TO temboard;
