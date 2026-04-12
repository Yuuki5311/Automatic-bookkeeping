package org.example.autobookkeeping;

import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.animation.ValueAnimator;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class FloatWindowService extends Service {

    private static final int STATE_COLLAPSED = 0;
    private static final int STATE_EXPANDED = 1;
    private static final int STATE_CONFIRMED = 2;

    private static final String ACTION_CATEGORIES = "org.example.autobookkeeping.CATEGORIES";
    private static final String ACTION_MANUAL_ENTRY = "org.example.autobookkeeping.MANUAL_ENTRY";

    private WindowManager _windowManager;
    private View _floatView;
    private WindowManager.LayoutParams _params;
    private Handler _mainHandler;
    private int _state = STATE_COLLAPSED;
    private boolean _initialized = false;

    private List<Map<String, Object>> _categories = new ArrayList<>();

    private int _collapsedSize;
    private int _expandedWidth;

    private float _touchStartX;
    private float _touchStartY;
    private int _touchStartParamY;
    private boolean _isDragging;
    private static final float DRAG_THRESHOLD_DP = 5f;

    private ValueAnimator _alphaAnimator;
    private ValueAnimator _slideAnimator;
    private int _halfSize;

    private TextView _collapsedBtn;
    private LinearLayout _expandedCard;
    private EditText _amountInput;
    private EditText _merchantInput;
    private Button _typeBtn;
    private LinearLayout _categoryContainer;
    private Button _confirmBtn;
    private TextView _confirmedText;

    private String _selectedType = "expense";
    private int _selectedCategoryId = 0;
    private int _selectedCategoryIndex = 0;

    private final Runnable _collapseToEdge = new Runnable() {
        @Override
        public void run() {
            startSlideAndFade(true);
        }
    };

    private final BroadcastReceiver _receiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (ACTION_CATEGORIES.equals(intent.getAction())) {
                String json = intent.getStringExtra("categories_json");
                if (json != null) updateCategories(json);
            }
        }
    };

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        _mainHandler = new Handler(Looper.getMainLooper());
        _windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);

        Map<String, Object> defaultCat = new HashMap<>();
        defaultCat.put("id", 0);
        defaultCat.put("name", "其他");
        _categories.add(defaultCat);

        _collapsedSize = dp(48);
        _expandedWidth = dp(280);
        _halfSize = _collapsedSize / 2;

        IntentFilter filter = new IntentFilter(ACTION_CATEGORIES);
        registerReceiver(_receiver, filter);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!_initialized) {
            _initialized = true;
            _mainHandler.post(new Runnable() {
                @Override
                public void run() {
                    initFloatWindow();
                }
            });
        }
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        _mainHandler.removeCallbacksAndMessages(null);
        if (_floatView != null) {
            try {
                _windowManager.removeView(_floatView);
            } catch (Exception ignored) {}
        }
        try {
            unregisterReceiver(_receiver);
        } catch (Exception ignored) {}
    }

    private void initFloatWindow() {
        _params = new WindowManager.LayoutParams(
                _collapsedSize,
                _collapsedSize,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT
        );
        _params.gravity = Gravity.TOP | Gravity.END;
        _params.x = 0;
        _params.y = dp(200);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        _floatView = root;

        _collapsedBtn = new TextView(this);
        _collapsedBtn.setText("记");
        _collapsedBtn.setTextColor(Color.WHITE);
        _collapsedBtn.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
        _collapsedBtn.setGravity(Gravity.CENTER);
        _collapsedBtn.setBackground(makeCircleDrawable(Color.parseColor("#FF6600")));
        LinearLayout.LayoutParams btnLp = new LinearLayout.LayoutParams(_collapsedSize, _collapsedSize);
        root.addView(_collapsedBtn, btnLp);

        _expandedCard = buildExpandedCard();
        _expandedCard.setVisibility(View.GONE);
        root.addView(_expandedCard);

        _floatView.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                return handleTouch(event);
            }
        });

        _windowManager.addView(_floatView, _params);
        scheduleCollapse();
    }

    private LinearLayout buildExpandedCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackgroundColor(Color.WHITE);
        card.setPadding(dp(12), dp(12), dp(12), dp(12));
        card.setElevation(dp(8));

        _amountInput = new EditText(this);
        _amountInput.setHint("金额（元）");
        _amountInput.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        _amountInput.addTextChangedListener(new android.text.TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}
            @Override public void afterTextChanged(android.text.Editable s) {
                updateConfirmBtn();
            }
        });
        card.addView(_amountInput, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));

        _typeBtn = new Button(this);
        _typeBtn.setText("支出");
        _typeBtn.setBackgroundColor(Color.parseColor("#FF6600"));
        _typeBtn.setTextColor(Color.WHITE);
        _typeBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                toggleType();
            }
        });
        LinearLayout.LayoutParams typeLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        typeLp.topMargin = dp(8);
        card.addView(_typeBtn, typeLp);

        _merchantInput = new EditText(this);
        _merchantInput.setHint("商家名称");
        _merchantInput.setInputType(android.text.InputType.TYPE_CLASS_TEXT);
        LinearLayout.LayoutParams merchantLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        merchantLp.topMargin = dp(8);
        card.addView(_merchantInput, merchantLp);

        HorizontalScrollView hsv = new HorizontalScrollView(this);
        LinearLayout.LayoutParams hsvLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        hsvLp.topMargin = dp(8);
        _categoryContainer = new LinearLayout(this);
        _categoryContainer.setOrientation(LinearLayout.HORIZONTAL);
        hsv.addView(_categoryContainer);
        card.addView(hsv, hsvLp);

        buildCategoryButtons();

        LinearLayout btnRow = new LinearLayout(this);
        btnRow.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams rowLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        rowLp.topMargin = dp(8);

        _confirmBtn = new Button(this);
        _confirmBtn.setText("确认");
        _confirmBtn.setEnabled(false);
        _confirmBtn.setBackgroundColor(Color.LTGRAY);
        _confirmBtn.setTextColor(Color.WHITE);
        _confirmBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                onConfirm();
            }
        });
        LinearLayout.LayoutParams confirmLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        btnRow.addView(_confirmBtn, confirmLp);

        Button cancelBtn = new Button(this);
        cancelBtn.setText("取消");
        cancelBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                switchToCollapsed();
            }
        });
        LinearLayout.LayoutParams cancelLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        cancelLp.leftMargin = dp(8);
        btnRow.addView(cancelBtn, cancelLp);

        card.addView(btnRow, rowLp);

        _confirmedText = new TextView(this);
        _confirmedText.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
        _confirmedText.setGravity(Gravity.CENTER);
        _confirmedText.setTextColor(Color.parseColor("#FF6600"));
        _confirmedText.setVisibility(View.GONE);
        LinearLayout.LayoutParams confirmedLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        confirmedLp.topMargin = dp(8);
        card.addView(_confirmedText, confirmedLp);

        return card;
    }

    private void buildCategoryButtons() {
        _categoryContainer.removeAllViews();
        for (int i = 0; i < _categories.size(); i++) {
            final int index = i;
            final int catId = (int) _categories.get(i).get("id");
            String catName = (String) _categories.get(i).get("name");
            Button btn = new Button(this);
            btn.setText(catName);
            btn.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            lp.rightMargin = dp(4);
            if (i == _selectedCategoryIndex) {
                btn.setBackgroundColor(Color.parseColor("#FF6600"));
                btn.setTextColor(Color.WHITE);
            } else {
                btn.setBackgroundColor(Color.LTGRAY);
                btn.setTextColor(Color.BLACK);
            }
            btn.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    _selectedCategoryIndex = index;
                    _selectedCategoryId = catId;
                    buildCategoryButtons();
                }
            });
            _categoryContainer.addView(btn, lp);
        }
    }

    private void toggleType() {
        if ("expense".equals(_selectedType)) {
            _selectedType = "income";
            _typeBtn.setText("收入");
            _typeBtn.setBackgroundColor(Color.parseColor("#4CAF50"));
        } else {
            _selectedType = "expense";
            _typeBtn.setText("支出");
            _typeBtn.setBackgroundColor(Color.parseColor("#FF6600"));
        }
    }

    private void updateConfirmBtn() {
        String amount = _amountInput.getText().toString().trim();
        boolean valid = !amount.isEmpty();
        _confirmBtn.setEnabled(valid);
        _confirmBtn.setBackgroundColor(valid ? Color.parseColor("#FF6600") : Color.LTGRAY);
    }

    private void onConfirm() {
        String amount = _amountInput.getText().toString().trim();
        String merchant = _merchantInput.getText().toString().trim();

        Intent intent = new Intent(ACTION_MANUAL_ENTRY);
        intent.setPackage("org.example.autobookkeeping");
        intent.putExtra("amount", amount);
        intent.putExtra("type", _selectedType);
        intent.putExtra("merchant", merchant);
        intent.putExtra("category_id", _selectedCategoryId);
        sendBroadcast(intent);

        switchToConfirmed(amount);
    }

    private void switchToCollapsed() {
        hideKeyboard();
        _state = STATE_COLLAPSED;
        _expandedCard.setVisibility(View.GONE);
        _collapsedBtn.setVisibility(View.VISIBLE);
        _confirmedText.setVisibility(View.GONE);

        _params.width = _collapsedSize;
        _params.height = _collapsedSize;
        _params.flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE;
        _params.x = 0;
        _floatView.setAlpha(1.0f);
        try {
            _windowManager.updateViewLayout(_floatView, _params);
        } catch (Exception ignored) {}

        scheduleCollapse();
    }

    private void switchToExpanded() {
        _mainHandler.removeCallbacks(_collapseToEdge);
        cancelAnimators();

        _state = STATE_EXPANDED;
        _collapsedBtn.setVisibility(View.GONE);
        _expandedCard.setVisibility(View.VISIBLE);
        _confirmedText.setVisibility(View.GONE);

        _amountInput.setText("");
        _merchantInput.setText("");
        _selectedType = "expense";
        _typeBtn.setText("支出");
        _typeBtn.setBackgroundColor(Color.parseColor("#FF6600"));
        _selectedCategoryIndex = 0;
        if (!_categories.isEmpty()) {
            _selectedCategoryId = (int) _categories.get(0).get("id");
        }
        buildCategoryButtons();
        updateConfirmBtn();

        _params.width = _expandedWidth;
        _params.height = WindowManager.LayoutParams.WRAP_CONTENT;
        _params.flags = WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH;
        _params.x = 0;
        _floatView.setAlpha(1.0f);
        try {
            _windowManager.updateViewLayout(_floatView, _params);
        } catch (Exception ignored) {}
    }

    private void switchToConfirmed(String amount) {
        _state = STATE_CONFIRMED;
        hideKeyboard();

        try {
            double val = Double.parseDouble(amount);
            _confirmedText.setText(String.format("已记录 ¥%.2f", val));
        } catch (NumberFormatException e) {
            _confirmedText.setText("已记录 ¥" + amount);
        }

        _confirmedText.setVisibility(View.VISIBLE);
        _amountInput.setVisibility(View.GONE);
        _typeBtn.setVisibility(View.GONE);
        _merchantInput.setVisibility(View.GONE);
        _confirmBtn.setVisibility(View.GONE);

        _mainHandler.postDelayed(new Runnable() {
            @Override
            public void run() {
                _amountInput.setVisibility(View.VISIBLE);
                _typeBtn.setVisibility(View.VISIBLE);
                _merchantInput.setVisibility(View.VISIBLE);
                _confirmBtn.setVisibility(View.VISIBLE);
                switchToCollapsed();
            }
        }, 2000);
    }

    private boolean handleTouch(MotionEvent event) {
        if (_state == STATE_EXPANDED) return false;
        if (_state == STATE_CONFIRMED) return true;

        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                _mainHandler.removeCallbacks(_collapseToEdge);
                cancelAnimators();
                _params.x = 0;
                _floatView.setAlpha(1.0f);
                try {
                    _windowManager.updateViewLayout(_floatView, _params);
                } catch (Exception ignored) {}
                _touchStartX = event.getRawX();
                _touchStartY = event.getRawY();
                _touchStartParamY = _params.y;
                _isDragging = false;
                return true;

            case MotionEvent.ACTION_MOVE:
                float dx = event.getRawX() - _touchStartX;
                float dy = event.getRawY() - _touchStartY;
                float threshold = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, DRAG_THRESHOLD_DP,
                        getResources().getDisplayMetrics());
                if (!_isDragging && (Math.abs(dx) > threshold || Math.abs(dy) > threshold)) {
                    _isDragging = true;
                }
                if (_isDragging) {
                    _params.y = _touchStartParamY + (int) dy;
                    try {
                        _windowManager.updateViewLayout(_floatView, _params);
                    } catch (Exception ignored) {}
                }
                return true;

            case MotionEvent.ACTION_UP:
                if (!_isDragging) {
                    switchToExpanded();
                } else {
                    scheduleCollapse();
                }
                return true;
        }
        return false;
    }

    private void scheduleCollapse() {
        _mainHandler.removeCallbacks(_collapseToEdge);
        _mainHandler.postDelayed(_collapseToEdge, 3000);
    }

    private void startSlideAndFade(boolean hide) {
        cancelAnimators();

        final int targetX = hide ? _halfSize : 0;
        final float targetAlpha = hide ? 0.3f : 1.0f;
        final int startX = _params.x;
        final float startAlpha = _floatView.getAlpha();

        _slideAnimator = ValueAnimator.ofInt(startX, targetX);
        _slideAnimator.setDuration(300);
        _slideAnimator.addUpdateListener(new ValueAnimator.AnimatorUpdateListener() {
            @Override
            public void onAnimationUpdate(ValueAnimator animation) {
                _params.x = (int) animation.getAnimatedValue();
                try {
                    _windowManager.updateViewLayout(_floatView, _params);
                } catch (Exception ignored) {}
            }
        });
        _slideAnimator.start();

        _alphaAnimator = ValueAnimator.ofFloat(startAlpha, targetAlpha);
        _alphaAnimator.setDuration(300);
        _alphaAnimator.addUpdateListener(new ValueAnimator.AnimatorUpdateListener() {
            @Override
            public void onAnimationUpdate(ValueAnimator animation) {
                _floatView.setAlpha((float) animation.getAnimatedValue());
            }
        });
        _alphaAnimator.start();
    }

    private void cancelAnimators() {
        if (_alphaAnimator != null) _alphaAnimator.cancel();
        if (_slideAnimator != null) _slideAnimator.cancel();
    }

    private void updateCategories(String json) {
        try {
            JSONArray arr = new JSONArray(json);
            List<Map<String, Object>> list = new ArrayList<>();
            for (int i = 0; i < arr.length(); i++) {
                JSONObject obj = arr.getJSONObject(i);
                Map<String, Object> map = new HashMap<>();
                map.put("id", obj.getInt("id"));
                map.put("name", obj.getString("name"));
                list.add(map);
            }
            if (!list.isEmpty()) {
                _categories = list;
                if (_state == STATE_EXPANDED) {
                    _mainHandler.post(new Runnable() {
                        @Override
                        public void run() {
                            _selectedCategoryIndex = 0;
                            _selectedCategoryId = (int) _categories.get(0).get("id");
                            buildCategoryButtons();
                        }
                    });
                }
            }
        } catch (Exception ignored) {}
    }

    private void hideKeyboard() {
        InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
        if (imm != null && _floatView != null) {
            imm.hideSoftInputFromWindow(_floatView.getWindowToken(), 0);
        }
    }

    private android.graphics.drawable.GradientDrawable makeCircleDrawable(int color) {
        android.graphics.drawable.GradientDrawable d = new android.graphics.drawable.GradientDrawable();
        d.setShape(android.graphics.drawable.GradientDrawable.OVAL);
        d.setColor(color);
        return d;
    }

    private int dp(int value) {
        return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, value,
                getResources().getDisplayMetrics());
    }
}
