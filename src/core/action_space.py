# FILE: src/core/action_space.py
class ActionSpace:
    def __init__(self):
        self.actions = [
            # 1. Structural
            "a'))", "--", " UNION", " SELECT", " NULL", ",",
            
            # 2. Tables (20 Bảng mục tiêu - ĐÃ ĐỒNG BỘ)
            " FROM sqlite_master", " FROM Users", " FROM SecurityAnswers", " FROM Addresses", 
            " FROM Cards", " FROM Challenges", " FROM BasketItems", " FROM Baskets", 
            " FROM Captchas", " FROM Complaints", " FROM Deliveries", " FROM Feedbacks", 
            " FROM ImageCaptchas", " FROM Memories", " FROM PrivacyRequests", " FROM Quantities", 
            " FROM Recycles", " FROM SecurityQuestions", " FROM Wallets", " FROM Products",

            # 3. Columns (Đã tối ưu cho Juice Shop)
            # Users specific
            " id", " username", " email", " password", " role", " totpSecret", 
            " lastLoginIp", " isActive", " deluxeToken", " type", " tbl_name", " sql",
            
            # Security / Address / Cards / Recycles
            " answer", " UserId", " SecurityQuestionId", " AddressId",
            " fullName", " mobileNum", " streetAddress", " city", " state", " country", " zipCode",
            " cardNum", " expMonth", " expYear",
            
            # Challenges / Hints / Quantities / Products
            " key", " name", " category", " description", " difficulty", " solved", " mitigationUrl",
            " quantity", " ProductId", " BasketId", " createdAt", " updatedAt", " limitPerUser",
            
            # Baskets / Captchas / Complaints / Deliveries
            " coupon", " captchaId", " captcha", 
            " message", " file", " price", " deluxePrice", " eta", " icon",
            
            # Feedbacks / ImageCaptchas / Memories / Privacy / Wallets
            " comment", " rating", " image", " caption", " imagePath",
            " deletionRequested", " isPickup", " date", 
            " question", " balance"
        ]
        self.num_actions = len(self.actions)

    def get_action_string(self, index):
        return self.actions[index]

    def get_action_space_size(self):
        return self.num_actions