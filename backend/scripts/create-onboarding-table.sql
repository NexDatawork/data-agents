-- Create onboarding_data table
CREATE TABLE IF NOT EXISTS onboarding_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    role TEXT NOT NULL,
    goals TEXT[] DEFAULT '{}',
    custom_goal TEXT DEFAULT '',
    data_types TEXT[] DEFAULT '{}',
    data_locations TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_onboarding_data_user_id ON onboarding_data(user_id);

-- Enable Row Level Security
ALTER TABLE onboarding_data ENABLE ROW LEVEL SECURITY;

-- Create policy for users to only access their own data
CREATE POLICY "Users can only access their own onboarding data" ON onboarding_data
    FOR ALL USING (auth.uid() = user_id);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_onboarding_data_updated_at 
    BEFORE UPDATE ON onboarding_data 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
