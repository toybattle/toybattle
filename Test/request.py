import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'auth'))
from db import supabase

def insert():
    try:
        response = (
            supabase.table("games")
            .insert([
                {"id": 2, "room_id": 1235},
            ])
            .execute()
        )
        return response
    except Exception as exception:
        return exception
    
# print(insert())

def update():
    try:
        response = (
            supabase.table("games")
            .update([
                {"room_id": 1236},
            ])
            .eq("id", 2)
            .execute()
        )
        return response
    except Exception as exception:
        return exception
    
# print(update())

def select():
    try:
        response = (
            supabase.table("games")
            .select("*")
            .execute()
        )
        return response
    except Exception as exception:
        return exception
    
# print(select())

def delete():
    try:
        response = (
            supabase.table("games")
            .delete()
            .eq("id", 2)
            .execute()
        )
        return response
    except Exception as exception:
        return exception
    
# print(delete())