package org.example.autobookkeeping;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.content.Intent;
import android.util.Log;
import java.util.ArrayList;

public class AutoBookkeepingAccessibilityService extends AccessibilityService {

    private static final String TAG = "AutoBookkeepAccSvc";
    private long lastEventTime = 0;
    private String lastCombinedText = "";

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED | AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.notificationTimeout = 500; // 500ms
        info.packageNames = new String[]{"com.eg.android.AlipayGphone", "com.tencent.mm"};
        info.flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS | AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
        setServiceInfo(info);
        Log.d(TAG, "Accessibility Service Connected");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;

        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) {
            Log.d(TAG, "rootNode is null (FLAG_SECURE or window not ready), pkg=" + event.getPackageName());
            return;
        }

        ArrayList<String> texts = new ArrayList<>();
        extractText(rootNode, texts);
        rootNode.recycle();

        String combinedText = String.join("\n", texts);
        Log.d(TAG, "onAccessibilityEvent pkg=" + event.getPackageName() + " textLen=" + combinedText.length());

        // Simple heuristic: if the screen contains payment successful indications
        if (combinedText.contains("支付成功") || combinedText.contains("付款成功")
                || combinedText.contains("交易详情") || combinedText.contains("账单详情")
                || combinedText.contains("凭证") || combinedText.contains("支付凭证")
                || combinedText.contains("转账成功") || combinedText.contains("已付款")) {
            long currentTime = System.currentTimeMillis();
            
            // Prevent sending the exact same text or sending too fast
            if (currentTime - lastEventTime < 3000 || combinedText.equals(lastCombinedText)) {
                return;
            }
            lastEventTime = currentTime;
            lastCombinedText = combinedText;
            
            Log.d(TAG, "Detected payment page: \n" + combinedText);
            
            String packageName = event.getPackageName() != null ? event.getPackageName().toString() : "unknown";
            
            Intent intent = new Intent("org.example.autobookkeeping.ACCESSIBILITY");
            intent.setPackage("org.example.autobookkeeping");
            intent.putExtra("package", packageName);
            intent.putExtra("text", combinedText);
            intent.putExtra("source", "accessibility");
            sendBroadcast(intent);
        }
    }

    private void extractText(AccessibilityNodeInfo node, ArrayList<String> texts) {
        if (node == null) return;
        if (node.getText() != null) {
            String txt = node.getText().toString().trim();
            if (!txt.isEmpty()) {
                texts.add(txt);
            }
        }
        if (node.getContentDescription() != null) {
             String desc = node.getContentDescription().toString().trim();
             if (!desc.isEmpty() && !texts.contains(desc)) {
                 texts.add(desc);
             }
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            extractText(child, texts);
            if (child != null) child.recycle();
        }
    }

    @Override
    public void onInterrupt() {
        Log.d(TAG, "Accessibility Service Interrupted");
    }
}