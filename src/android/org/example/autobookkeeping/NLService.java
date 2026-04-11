package org.example.autobookkeeping;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.content.Intent;
import android.app.Notification;
import android.os.Bundle;
import android.util.Log;

public class NLService extends NotificationListenerService {
    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        String packageName = sbn.getPackageName();
        if (packageName == null) return;
        
        if (packageName.toLowerCase().contains("alipay") || packageName.contains("tencent.mm")) {
            Notification notification = sbn.getNotification();
            if (notification == null) return;
            Bundle extras = notification.extras;
            if (extras == null) return;
            
            CharSequence text = extras.getCharSequence(Notification.EXTRA_TEXT);
            CharSequence title = extras.getCharSequence(Notification.EXTRA_TITLE);
            
            String fullText = "";
            if (title != null) fullText += title.toString() + " ";
            if (text != null) fullText += text.toString();
            
            Log.d("NLService", "AutoBookkeeping received: " + fullText);
            
            Intent intent = new Intent("org.example.autobookkeeping.NOTIFICATION");
            intent.setPackage("org.example.autobookkeeping");
            intent.putExtra("package", packageName);
            intent.putExtra("text", fullText);
            intent.putExtra("source", "notification");
            sendBroadcast(intent);
        }
    }
    
    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {}
}
