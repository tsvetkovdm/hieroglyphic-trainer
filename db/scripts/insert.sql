\copy "role"("name") FROM 'C:/Users/ench/Desktop/hieroglyphic-trainer/db/csv/role.csv' DELIMITER ';' CSV HEADER;
\copy "training_mode"("name", "access_level", "description") FROM 'C:/Users/ench/Desktop/hieroglyphic-trainer/db/csv/training_mode.csv' DELIMITER ';' CSV HEADER;
\copy "radical_group"("name", "slug", "description") FROM 'C:/Users/ench/Desktop/hieroglyphic-trainer/db/csv/radical_group.csv' DELIMITER ';' CSV HEADER;
\copy "user"("username", "password", "first_name", "last_name", "email", "date_of_birth", "role_id") FROM 'C:/Users/ench/Desktop/hieroglyphic-trainer/db/csv/user.csv' DELIMITER ';' CSV HEADER;
\copy "training_session"("user_id", "mode_id", "date_started", "date_ended", "result") FROM 'C:/Users/ench/Desktop/hieroglyphic-trainer/db/csv/training_session.csv' DELIMITER ';' CSV HEADER;
\copy "learning_object"("symbol", "pinyin", "meaning", "stroke_order_image_url", "description", "slug", "group_id") FROM 'C:/Users/ench/Desktop/hieroglyphic-trainer/db/csv/learning_object.csv' DELIMITER ';' CSV HEADER;
\copy "training_item"("session_id", "object_id") FROM 'C:/Users/ench/Desktop/hieroglyphic-trainer/db/csv/training_item.csv' DELIMITER ';' CSV HEADER;
\copy "user_selection"("user_id", "object_id", "saved_name") FROM 'C:/Users/ench/Desktop/hieroglyphic-trainer/db/csv/user_selection.csv' DELIMITER ';' CSV HEADER;