import { getSupabaseClient } from "./supabase"

export interface FileMetadata {
  id?: string
  name: string
  url: string
  user_id: string
  size: number
  created_at?: string
}

// Upload file to Supabase Storage and save metadata
export async function uploadFileToStorage(
  file: File,
  userId: string,
): Promise<{ success: boolean; data?: FileMetadata; error?: string }> {
  try {
    const supabase = getSupabaseClient()
    if (!supabase) {
      return { success: false, error: "Supabase not configured" }
    }

    // Create unique filename with timestamp
    const timestamp = Date.now()
    const fileExtension = file.name.split(".").pop()
    const uniqueFileName = `${userId}/${timestamp}_${file.name}`

    // Upload file to storage bucket
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from("user-datasets")
      .upload(uniqueFileName, file, {
        cacheControl: "3600",
        upsert: false,
      })

    if (uploadError) {
      console.error("Upload error:", uploadError)
      return { success: false, error: uploadError.message }
    }

    // Get public URL
    const { data: urlData } = supabase.storage.from("user-datasets").getPublicUrl(uniqueFileName)

    if (!urlData?.publicUrl) {
      return { success: false, error: "Failed to get public URL" }
    }

    // Save metadata to database
    const fileMetadata: Omit<FileMetadata, "id" | "created_at"> = {
      name: file.name,
      url: urlData.publicUrl,
      user_id: userId,
      size: file.size,
    }

    const { data: dbData, error: dbError } = await supabase.from("user_files").insert([fileMetadata]).select().single()

    if (dbError) {
      console.error("Database error:", dbError)
      // Try to clean up uploaded file if database insert fails
      await supabase.storage.from("user-datasets").remove([uniqueFileName])
      return { success: false, error: dbError.message }
    }

    return { success: true, data: dbData }
  } catch (error) {
    console.error("Unexpected error in uploadFileToStorage:", error)
    return { success: false, error: error instanceof Error ? error.message : "Unknown error" }
  }
}

// Get user's uploaded files
export async function getUserFiles(
  userId: string,
): Promise<{ success: boolean; data?: FileMetadata[]; error?: string }> {
  try {
    const supabase = getSupabaseClient()
    if (!supabase) {
      return { success: false, error: "Supabase not configured" }
    }

    const { data, error } = await supabase
      .from("user_files")
      .select("*")
      .eq("user_id", userId)
      .order("created_at", { ascending: false })

    if (error) {
      console.error("Error fetching user files:", error)
      return { success: false, error: error.message }
    }

    return { success: true, data: data || [] }
  } catch (error) {
    console.error("Unexpected error in getUserFiles:", error)
    return { success: false, error: error instanceof Error ? error.message : "Unknown error" }
  }
}

// Delete file from storage and database
export async function deleteUserFile(fileId: string, userId: string): Promise<{ success: boolean; error?: string }> {
  try {
    const supabase = getSupabaseClient()
    if (!supabase) {
      return { success: false, error: "Supabase not configured" }
    }

    // First get the file metadata to get the storage path
    const { data: fileData, error: fetchError } = await supabase
      .from("user_files")
      .select("*")
      .eq("id", fileId)
      .eq("user_id", userId)
      .single()

    if (fetchError || !fileData) {
      return { success: false, error: "File not found" }
    }

    // Extract storage path from URL
    const url = new URL(fileData.url)
    const pathParts = url.pathname.split("/")
    const bucketIndex = pathParts.findIndex((part) => part === "user-datasets")
    if (bucketIndex === -1 || bucketIndex === pathParts.length - 1) {
      return { success: false, error: "Invalid file URL format" }
    }
    const storagePath = pathParts.slice(bucketIndex + 1).join("/")

    // Delete from storage
    const { error: storageError } = await supabase.storage.from("user-datasets").remove([storagePath])

    if (storageError) {
      console.error("Storage deletion error:", storageError)
      // Continue with database deletion even if storage deletion fails
    }

    // Delete from database
    const { error: dbError } = await supabase.from("user_files").delete().eq("id", fileId).eq("user_id", userId)

    if (dbError) {
      console.error("Database deletion error:", dbError)
      return { success: false, error: dbError.message }
    }

    return { success: true }
  } catch (error) {
    console.error("Unexpected error in deleteUserFile:", error)
    return { success: false, error: error instanceof Error ? error.message : "Unknown error" }
  }
}
