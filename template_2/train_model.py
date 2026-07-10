from config import (
    PROCESSED_DATA_PATH,
    MODEL_NAME,
    MODEL_PATH,
    TEST_SIZE,
    RANDOM_STATE,
)


def load_data(data_path):
    """Đọc dữ liệu đã được xử lý."""
    # TODO: Đọc JSON, CSV hoặc định dạng khác.
    # TODO: Trả về dữ liệu thô đã xử lý.
    pass


def prepare_training_data(data):
    """
    Chuyển dữ liệu 5 cores sang định dạng phù hợp với kỹ thuật được chọn.

    Returns:
        X: dữ liệu đầu vào
        y: nhãn LOC
    """
    # TODO:
    # - Machine Learning: flatten thành X, y.
    # - Deep Learning: chuyển thành tensor.
    # - LLM: tạo text hoặc prompt.
    # - Rule-based: giữ dạng dictionary/rule input.
    pass


def split_data(X, y, test_size, random_state):
    """Chia dữ liệu train và test."""
    # TODO:
    # - Có thể dùng train_test_split.
    # - Có thể thay bằng cross-validation.
    pass


def create_model(model_name):
    """Khởi tạo model hoặc kỹ thuật được chọn."""
    # TODO:
    # - Random Forest
    # - Logistic Regression
    # - XGBoost
    # - Neural Network
    # - Kỹ thuật khác
    pass


def train_model(model, X_train, y_train):
    """Huấn luyện model và trả về model đã train."""
    # TODO:
    # - sklearn: model.fit(X_train, y_train)
    # - Deep Learning: viết training loop riêng.
    pass


def evaluate_model(model, X_test, y_test):
    """Đánh giá model và trả về kết quả metrics."""
    # TODO:
    # - Accuracy
    # - Precision
    # - Recall
    # - F1-score
    # - Confusion Matrix
    # - Cohen's Kappa
    pass


def save_model(model, model_path):
    """Lưu model sau khi train."""
    # TODO:
    # - joblib
    # - pickle
    # - save_weights
    # - save_pretrained
    pass


def main():
    # 1. Load dữ liệu
    data = load_data(PROCESSED_DATA_PATH)

    # 2. Chuẩn bị dữ liệu train
    X, y = prepare_training_data(data)

    # 3. Chia dữ liệu
    X_train, X_test, y_train, y_test = split_data(
        X=X,
        y=y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    # 4. Khởi tạo model
    model = create_model(MODEL_NAME)

    # 5. Train
    trained_model = train_model(
        model=model,
        X_train=X_train,
        y_train=y_train,
    )

    # 6. Đánh giá
    evaluate_model(
        model=trained_model,
        X_test=X_test,
        y_test=y_test,
    )

    # 7. Lưu model
    save_model(
        model=trained_model,
        model_path=MODEL_PATH,
    )


if __name__ == "__main__":
    main()
