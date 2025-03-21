from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from db_con import db

# Colecciones de MongoDB
users_collection = db["users"]
orders_collection = db["orders"]
boxes_collection = db["boxes"]
users_temp_collection = db["users_temp"]