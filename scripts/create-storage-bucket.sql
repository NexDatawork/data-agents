-- Create storage bucket for user datasets
INSERT INTO storage.buckets (id, name, public)
VALUES ('user-datasets', 'user-datasets', true);

-- Create policy to allow authenticated users to upload files
CREATE POLICY "Users can upload their own files" ON storage.objects
FOR INSERT WITH CHECK (
  bucket_id = 'user-datasets' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Create policy to allow users to view their own files
CREATE POLICY "Users can view their own files" ON storage.objects
FOR SELECT USING (
  bucket_id = 'user-datasets' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Create policy to allow users to delete their own files
CREATE POLICY "Users can delete their own files" ON storage.objects
FOR DELETE USING (
  bucket_id = 'user-datasets' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Create table for file metadata
CREATE TABLE IF NOT EXISTS user_files (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  size BIGINT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON user_files(user_id);
CREATE INDEX IF NOT EXISTS idx_user_files_created_at ON user_files(created_at);

-- Enable RLS on user_files table
ALTER TABLE user_files ENABLE ROW LEVEL SECURITY;

-- Create policy for user_files table
CREATE POLICY "Users can manage their own files" ON user_files
FOR ALL USING (auth.uid() = user_id);
