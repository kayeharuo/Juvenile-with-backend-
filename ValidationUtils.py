from Db_connection import get_db_connection

def check_email_exists(email):
    if not email or not email.strip():
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM JUVENILE_GUARDIAN_PROFILE WHERE GRDN_EMAIL_ADDRESS = %s LIMIT 1",
            (email.strip(),)
        )
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print(f"Error checking email: {e}")
        if conn:
            conn.close()
        return False

def check_case_number_exists(case_no):
    if not case_no or not case_no.strip():
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM OFFENSE_INFORMATION WHERE OFFNS_CASE_RECORD_NO = %s LIMIT 1",
            (case_no.strip(),)
        )
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print(f"Error checking case number: {e}")
        if conn:
            conn.close()
        return False

def check_embedding_similarity(new_embedding, threshold=0.4):
    #Check if a similar embedding already exists in database
    #Returns (exists, juv_id) - exists=True if similar face found
    
    if not new_embedding:
        return False, None
    
    conn = get_db_connection()
    if not conn:
        return False, None
    
    try:
        import numpy as np
        import face_recognition
        
        cursor = conn.cursor()
        cursor.execute("SELECT JUV_ID, EMBEDDING FROM FACIAL_DATA")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not results:
            return False, None
        
        new_emb_array = np.array(eval(new_embedding))
        
        for juv_id, stored_embedding_str in results:
            try:
                stored_emb_array = np.array(eval(stored_embedding_str))
                distance = face_recognition.face_distance([stored_emb_array], new_emb_array)[0]
                if distance < threshold:
                    print(f"Similar face found! JUV_ID: {juv_id}, Distance: {distance}")
                    return True, juv_id
                    
            except Exception as e:
                print(f"Error comparing with JUV_ID {juv_id}: {e}")
                continue
        
        return False, None
        
    except Exception as e:
        print(f"Error checking embedding similarity: {e}")
        if conn:
            conn.close()
        return False, None