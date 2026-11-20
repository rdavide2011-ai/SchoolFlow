#!/usr/bin/env python3
"""Aggiunge al progetto Android generato da Capacitor i 3 widget SchoolFlow.
Uso: python3 android-widgets/setup_widgets.py [cartella_android]   (default: android)
Crea: plugin Capacitor SchoolFlowWidgets, 3 provider, layout, XML, manifest, MainActivity."""
import re, sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "android")
PKG = "com.rivapps.schoolflow"
APP = ROOT / "app" / "src" / "main"
JAVA = APP / "java" / PKG.replace(".", "/")
RES = APP / "res"
JAVA.mkdir(parents=True, exist_ok=True)
for d in ("layout", "drawable", "xml", "values"):
    (RES / d).mkdir(parents=True, exist_ok=True)


def w(path, text):
    path.write_text(text.strip("\n") + "\n", encoding="utf-8")


# ---------------------------------------------------------------- Java
w(JAVA / "MainActivity.java", f"""
package {PKG};

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {{
    @Override
    public void onCreate(Bundle savedInstanceState) {{
        registerPlugin(SchoolFlowWidgetsPlugin.class);
        super.onCreate(savedInstanceState);
    }}
}}
""")

w(JAVA / "SfWidgets.java", f"""
package {PKG};

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import java.text.NumberFormat;
import java.util.Locale;
import org.json.JSONObject;

final class SfWidgets {{
    static final String PREFS = "schoolflow_widgets";
    static final String KEY = "data";
    static final int GREEN = 0xFF34C38F;
    static final int ORANGE = 0xFFF5A524;
    static final int RED = 0xFFEF5B5B;
    static final int WHITE = 0xFFFFFFFF;
    static final int MUTED = 0xFFB9B3E8;

    private SfWidgets() {{}}

    static void save(Context c, String json) {{
        c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY, json).apply();
    }}

    static JSONObject load(Context c) {{
        try {{
            String s = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY, null);
            return s == null ? null : new JSONObject(s);
        }} catch (Exception e) {{
            return null;
        }}
    }}

    static String fmt(double v) {{
        NumberFormat nf = NumberFormat.getNumberInstance(Locale.ITALY);
        nf.setMaximumFractionDigits(2);
        nf.setMinimumFractionDigits(0);
        return nf.format(v);
    }}

    static int color(double v) {{
        return v >= 6 ? GREEN : (v >= 5 ? ORANGE : RED);
    }}

    static PendingIntent open(Context c) {{
        Intent i = c.getPackageManager().getLaunchIntentForPackage(c.getPackageName());
        if (i == null) i = new Intent();
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
        return PendingIntent.getActivity(c, 0, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }}

    static int id(Context c, String name) {{
        return c.getResources().getIdentifier(name, "id", c.getPackageName());
    }}

    static void refreshAll(Context c) {{
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        int[] a = m.getAppWidgetIds(new ComponentName(c, OverallWidgetProvider.class));
        if (a != null && a.length > 0) m.updateAppWidget(a, OverallWidgetProvider.build(c));
        int[] b = m.getAppWidgetIds(new ComponentName(c, SubjectsWidgetProvider.class));
        if (b != null && b.length > 0) m.updateAppWidget(b, SubjectsWidgetProvider.build(c));
        int[] d = m.getAppWidgetIds(new ComponentName(c, LastWidgetProvider.class));
        if (d != null && d.length > 0) m.updateAppWidget(d, LastWidgetProvider.build(c));
    }}
}}
""")

w(JAVA / "OverallWidgetProvider.java", f"""
package {PKG};

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.widget.RemoteViews;
import org.json.JSONObject;

public class OverallWidgetProvider extends AppWidgetProvider {{
    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] ids) {{
        manager.updateAppWidget(ids, build(context));
    }}

    static RemoteViews build(Context c) {{
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.widget_overall);
        JSONObject d = SfWidgets.load(c);
        String value = "—";
        String sub = "Apri SchoolFlow";
        int col = SfWidgets.MUTED;
        if (d != null) {{
            if (!d.isNull("o")) {{
                double o = d.optDouble("o");
                value = SfWidgets.fmt(o);
                col = SfWidgets.color(o);
            }}
            int cnt = d.optInt("c");
            sub = cnt == 0 ? "Aggiungi i tuoi primi voti"
                    : d.optString("p") + " · " + cnt + (cnt == 1 ? " voto" : " voti");
        }}
        v.setTextViewText(R.id.w_value, value);
        v.setTextColor(R.id.w_value, col);
        v.setTextViewText(R.id.w_sub, sub);
        v.setOnClickPendingIntent(R.id.w_root, SfWidgets.open(c));
        return v;
    }}
}}
""")

w(JAVA / "SubjectsWidgetProvider.java", f"""
package {PKG};

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.view.View;
import android.widget.RemoteViews;
import org.json.JSONArray;
import org.json.JSONObject;

public class SubjectsWidgetProvider extends AppWidgetProvider {{
    static final int ROWS = 7;

    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] ids) {{
        manager.updateAppWidget(ids, build(context));
    }}

    static RemoteViews build(Context c) {{
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.widget_subjects);
        JSONObject d = SfWidgets.load(c);
        JSONArray s = d == null ? null : d.optJSONArray("s");
        v.setTextViewText(R.id.w_title, d == null ? "Materie" : "Materie · " + d.optString("p"));
        int n = s == null ? 0 : s.length();
        int shown = n > ROWS ? ROWS - 1 : n;
        for (int i = 0; i < ROWS; i++) {{
            int row = SfWidgets.id(c, "w_r" + i);
            if (i < shown) {{
                JSONObject o = s.optJSONObject(i);
                v.setViewVisibility(row, View.VISIBLE);
                v.setTextViewText(SfWidgets.id(c, "w_r" + i + "_n"), o.optString("n"));
                if (o.isNull("a")) {{
                    v.setTextViewText(SfWidgets.id(c, "w_r" + i + "_a"), "—");
                    v.setTextColor(SfWidgets.id(c, "w_r" + i + "_a"), SfWidgets.MUTED);
                }} else {{
                    double a = o.optDouble("a");
                    v.setTextViewText(SfWidgets.id(c, "w_r" + i + "_a"), SfWidgets.fmt(a));
                    v.setTextColor(SfWidgets.id(c, "w_r" + i + "_a"), SfWidgets.color(a));
                }}
            }} else if (i == shown && n > ROWS) {{
                v.setViewVisibility(row, View.VISIBLE);
                v.setTextViewText(SfWidgets.id(c, "w_r" + i + "_n"), "+ altre " + (n - shown) + " materie");
                v.setTextViewText(SfWidgets.id(c, "w_r" + i + "_a"), "");
            }} else {{
                v.setViewVisibility(row, View.GONE);
            }}
        }}
        v.setViewVisibility(R.id.w_empty, n == 0 ? View.VISIBLE : View.GONE);
        v.setOnClickPendingIntent(R.id.w_root, SfWidgets.open(c));
        return v;
    }}
}}
""")

w(JAVA / "LastWidgetProvider.java", f"""
package {PKG};

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.view.View;
import android.widget.RemoteViews;
import org.json.JSONArray;
import org.json.JSONObject;

public class LastWidgetProvider extends AppWidgetProvider {{
    static final int ROWS = 5;

    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] ids) {{
        manager.updateAppWidget(ids, build(context));
    }}

    static RemoteViews build(Context c) {{
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.widget_last);
        JSONObject d = SfWidgets.load(c);
        JSONArray l = d == null ? null : d.optJSONArray("l");
        int n = l == null ? 0 : l.length();
        for (int i = 0; i < ROWS; i++) {{
            int row = SfWidgets.id(c, "w_r" + i);
            if (i < n) {{
                JSONObject o = l.optJSONObject(i);
                double val = o.optDouble("v");
                v.setViewVisibility(row, View.VISIBLE);
                v.setTextViewText(SfWidgets.id(c, "w_r" + i + "_n"), o.optString("s"));
                v.setTextViewText(SfWidgets.id(c, "w_r" + i + "_d"), o.optString("d"));
                v.setTextViewText(SfWidgets.id(c, "w_r" + i + "_a"), SfWidgets.fmt(val));
                v.setTextColor(SfWidgets.id(c, "w_r" + i + "_a"), SfWidgets.color(val));
            }} else {{
                v.setViewVisibility(row, View.GONE);
            }}
        }}
        v.setViewVisibility(R.id.w_empty, n == 0 ? View.VISIBLE : View.GONE);
        v.setOnClickPendingIntent(R.id.w_root, SfWidgets.open(c));
        return v;
    }}
}}
""")

w(JAVA / "SchoolFlowWidgetsPlugin.java", f"""
package {PKG};

import android.appwidget.AppWidgetManager;
import android.content.ComponentName;
import android.os.Build;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "SchoolFlowWidgets")
public class SchoolFlowWidgetsPlugin extends Plugin {{
    @PluginMethod
    public void update(PluginCall call) {{
        String json = call.getString("json");
        if (json == null) {{
            call.reject("json mancante");
            return;
        }}
        SfWidgets.save(getContext(), json);
        SfWidgets.refreshAll(getContext());
        call.resolve();
    }}

    @PluginMethod
    public void requestPin(PluginCall call) {{
        String type = call.getString("type", "overall");
        Class<?> target = OverallWidgetProvider.class;
        if ("subjects".equals(type)) target = SubjectsWidgetProvider.class;
        else if ("last".equals(type)) target = LastWidgetProvider.class;
        JSObject r = new JSObject();
        AppWidgetManager m = AppWidgetManager.getInstance(getContext());
        boolean supported = Build.VERSION.SDK_INT >= 26 && m.isRequestPinAppWidgetSupported();
        r.put("supported", supported);
        if (supported) {{
            boolean ok = m.requestPinAppWidget(new ComponentName(getContext(), target), null, null);
            r.put("requested", ok);
        }}
        call.resolve(r);
    }}
}}
""")

# ---------------------------------------------------------------- risorse
w(RES / "drawable" / "sf_widget_bg.xml", """
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient android:angle="315" android:startColor="#FF2A2257" android:endColor="#FF14112B" />
    <corners android:radius="22dp" />
    <stroke android:width="1dp" android:color="#33FFFFFF" />
</shape>
""")

w(RES / "values" / "sf_widget_strings.xml", """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="sf_widget_overall_desc">La tua media generale</string>
    <string name="sf_widget_subjects_desc">La media di ogni materia</string>
    <string name="sf_widget_last_desc">Gli ultimi voti che hai preso</string>
</resources>
""")

NS = 'xmlns:android="http://schemas.android.com/apk/res/android"'

w(RES / "layout" / "widget_overall.xml", f"""
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout {NS}
    android:id="@+id/w_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@drawable/sf_widget_bg"
    android:gravity="center"
    android:orientation="vertical"
    android:padding="12dp">
    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="MEDIA GENERALE"
        android:textColor="#FFB9B3E8"
        android:textSize="10sp"
        android:textStyle="bold" />
    <TextView
        android:id="@+id/w_value"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="—"
        android:textColor="#FFFFFFFF"
        android:textSize="42sp"
        android:textStyle="bold" />
    <TextView
        android:id="@+id/w_sub"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:gravity="center"
        android:maxLines="2"
        android:text="Apri SchoolFlow"
        android:textColor="#FFB9B3E8"
        android:textSize="11sp" />
</LinearLayout>
""")


def rows(count, with_date):
    out = []
    for i in range(count):
        date = f"""
        <TextView
            android:id="@+id/w_r{i}_d"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginEnd="10dp"
            android:textColor="#FFB9B3E8"
            android:textSize="11sp" />""" if with_date else ""
        out.append(f"""
    <LinearLayout
        android:id="@+id/w_r{i}"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1"
        android:gravity="center_vertical"
        android:orientation="horizontal"
        android:visibility="gone">
        <TextView
            android:id="@+id/w_r{i}_n"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:ellipsize="end"
            android:maxLines="1"
            android:textColor="#FFFFFFFF"
            android:textSize="13sp" />{date}
        <TextView
            android:id="@+id/w_r{i}_a"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:textColor="#FFFFFFFF"
            android:textSize="15sp"
            android:textStyle="bold" />
    </LinearLayout>""")
    return "".join(out)


def list_layout(title_xml, count, with_date):
    return f"""
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout {NS}
    android:id="@+id/w_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@drawable/sf_widget_bg"
    android:orientation="vertical"
    android:padding="14dp">
{title_xml}
{rows(count, with_date)}
    <TextView
        android:id="@+id/w_empty"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1"
        android:gravity="center"
        android:text="Aggiungi i tuoi primi voti"
        android:textColor="#FFB9B3E8"
        android:textSize="12sp"
        android:visibility="gone" />
</LinearLayout>
"""


title_subjects = """    <TextView
        android:id="@+id/w_title"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginBottom="6dp"
        android:ellipsize="end"
        android:maxLines="1"
        android:text="Materie"
        android:textColor="#FFB9B3E8"
        android:textSize="11sp"
        android:textStyle="bold" />"""
title_last = title_subjects.replace('android:id="@+id/w_title"\n        ', "").replace('"Materie"', '"ULTIMI VOTI"')

w(RES / "layout" / "widget_subjects.xml", list_layout(title_subjects, 7, False))
w(RES / "layout" / "widget_last.xml", list_layout(title_last, 5, True))


def info(name, cw, ch, minw, minh, desc, layout):
    w(RES / "xml" / f"{name}.xml", f"""
<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider {NS}
    android:minWidth="{minw}dp"
    android:minHeight="{minh}dp"
    android:targetCellWidth="{cw}"
    android:targetCellHeight="{ch}"
    android:minResizeWidth="{minw}dp"
    android:minResizeHeight="{minh}dp"
    android:resizeMode="horizontal|vertical"
    android:updatePeriodMillis="0"
    android:widgetCategory="home_screen"
    android:description="@string/{desc}"
    android:initialLayout="@layout/{layout}"
    android:previewLayout="@layout/{layout}" />
""")


info("sf_widget_overall_info", 2, 2, 110, 110, "sf_widget_overall_desc", "widget_overall")
info("sf_widget_subjects_info", 4, 3, 250, 180, "sf_widget_subjects_desc", "widget_subjects")
info("sf_widget_last_info", 4, 2, 250, 110, "sf_widget_last_desc", "widget_last")

# ---------------------------------------------------------------- manifest
manifest = APP / "AndroidManifest.xml"
text = manifest.read_text(encoding="utf-8")
if "OverallWidgetProvider" not in text:
    recv = ""
    for cls, res in (("OverallWidgetProvider", "sf_widget_overall_info"),
                     ("SubjectsWidgetProvider", "sf_widget_subjects_info"),
                     ("LastWidgetProvider", "sf_widget_last_info")):
        recv += f"""
        <receiver android:name=".{cls}" android:exported="false">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data android:name="android.appwidget.provider" android:resource="@xml/{res}" />
        </receiver>
"""
    new, n = re.subn(r"</application>", lambda m: recv + "    </application>", text, count=1)
    if n != 1:
        raise SystemExit("AndroidManifest: </application> non trovato")
    manifest.write_text(new, encoding="utf-8")
print("Widget SchoolFlow aggiunti a", ROOT)
