// Test connection and create a simple table
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://cycnichledvqbxevrwnt.supabase.co'
const supabaseKey = 'your-anon-key-here'

const supabase = createClient(supabaseUrl, supabaseKey)

// Test query - run this in SQL Editor:
/*
CREATE TABLE IF NOT EXISTS test_table (
  id SERIAL PRIMARY KEY,
  name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

SELECT * FROM test_table;
*/

// Or try inserting:
async function test() {
  const { data, error } = await supabase
    .from('test_table')
    .insert([{ name: 'test' }])
    .select()
  
  if (error) {
    console.log('Error:', error.message)
  } else {
    console.log('Success:', data)
  }
}

test()
