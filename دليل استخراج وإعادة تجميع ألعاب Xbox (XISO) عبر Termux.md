# الدليل الشامل لاستخراج وإعادة تجميع ألعاب Xbox (XISO) عبر Termux

## لماذا تظهر ملفات Xbox ISO فارغة في برامج فك الضغط العادية؟
تستخدم أقراص ألعاب **Xbox الأصلي** و **Xbox 360** نظام ملفات خاصاً بشركة مايكروسوفت يُسمى **XDVDFS (XISO)** بدلاً من أنظمة `ISO9660` أو `UDF` التقليدية. لذلك، تفشل برامج فك الضغط العادية (مثل ZArchiver و WinRAR) في قراءتها، ونحتاج إلى أداة **`extract-xiso`** المتخصصة لاستخراج الملفات أو إعادة تجميعها بشكل صحيح.

> **ملاحظة تقنية مهمة حول بيئة Termux:**
> عند بناء أداة `extract-xiso` داخل تطبيق Termux، يتعرف برنامج `cmake` على النظام باسم `Android` بدلاً من `Linux`، مما يسبب توقف البناء بخطأ `#error unknown target`. تم حل هذه المشكلة في السكربتات أدناه بتمرير العلم `-DCMAKE_C_FLAGS="-D__LINUX__"` صراحةً للمترجم.

---

## الخطوة التمهيدية: منح Termux صلاحية الوصول إلى ذاكرة الهاتف
نفّذ هذا الأمر مرة واحدة فقط في Termux ووافق على نافذة الصلاحيات المنبثقة:

```bash
termux-setup-storage
```

---

## أولاً: سكربت التثبيت والاستخراج الكامل (نسخ ولصق دفعة واحدة)
يقوم هذا السكربت بالخطوات التالية تلقائياً:
1. التحقق من وجود أداة `extract-xiso`، وتثبيت أدوات البناء وتجميع الأداة تلقائياً إذا لم تكن مثبتة.
2. التحقق من وجود ملف اللعبة في المسار المحدد.
3. استخراج جميع ملفات اللعبة إلى المجلد الهدف.
4. فحص المجلد المستخرج للتأكد من وجود ملف التشغيل الرئيسي `default.xbe` وعرض عدد الملفات والحجم النهائي.

```bash
cat << 'EOF' > ~/extract_xiso_game.sh
#!/data/data/com.termux/files/usr/bin/bash
set -e

ISO_PATH="/storage/emulated/0/Download/logs/game.iso"
OUT_DIR="/storage/emulated/0/Download/logs/Black_Xbox_Extracted"

echo "=========================================="
echo "1. التحقق من أداة extract-xiso وتثبيتها..."
echo "=========================================="
if ! command -v extract-xiso >/dev/null 2>&1; then
    apt-get update -y
    apt-get install -y -o Dpkg::Options::="--force-confnew" git cmake make clang

    rm -rf ~/extract-xiso
    git clone --depth 1 https://github.com/XboxDev/extract-xiso.git ~/extract-xiso
    mkdir -p ~/extract-xiso/build
    cd ~/extract-xiso/build
    cmake .. -DCMAKE_C_FLAGS="-D__LINUX__"
    make -j$(nproc)
    cp extract-xiso "$PREFIX/bin/extract-xiso"
    chmod +x "$PREFIX/bin/extract-xiso"
    cd ~
    rm -rf ~/extract-xiso
    echo "تم تثبيت أداة extract-xiso بنجاح."
else
    echo "أداة extract-xiso مثبتة مسبقاً وجاهزة."
fi

echo "=========================================="
echo "2. التحقق من ملف اللعبة وبدء الاستخراج..."
echo "=========================================="
if [ ! -f "$ISO_PATH" ]; then
    echo "خطأ: الملف غير موجود في المسار: $ISO_PATH"
    echo "تأكد من تنفيذ أمر termux-setup-storage ومن وجود الملف."
    exit 1
fi

mkdir -p "$OUT_DIR"
extract-xiso -d "$OUT_DIR" "$ISO_PATH"

echo "=========================================="
echo "3. التحقق من سلامة الملفات المستخرجة..."
echo "=========================================="
if [ -f "$OUT_DIR/default.xbe" ]; then
    FILE_COUNT=$(find "$OUT_DIR" -type f | wc -l)
    FOLDER_SIZE=$(du -sh "$OUT_DIR" | cut -f1)
    echo "تم الاستخراج بنجاح!"
    echo "المسار: $OUT_DIR"
    echo "ملف التشغيل الرئيسي: default.xbe (موجود)"
    echo "عدد الملفات المستخرجة: $FILE_COUNT"
    echo "الحجم الإجمالي للمجلد: $FOLDER_SIZE"
else
    echo "تحذير: لم يتم العثور على ملف default.xbe بعد الاستخراج!"
    exit 1
fi
echo "=========================================="
EOF
chmod +x ~/extract_xiso_game.sh && bash ~/extract_xiso_game.sh
```

### لماذا يكون حجم المجلد المستخرج أصغر قليلاً من ملف الـ ISO؟
من الطبيعي أن يكون حجم المجلد المستخرج (مثلاً `1.58 GB`) أصغر بنحو `80 - 100 MB` من ملف الـ ISO الأصلي (`1.67 GB`)، وذلك للأسباب التالية:
* **إزالة حشو القطاعات (Sector Padding):** نظام ملفات الإكس بوكس يملأ الفراغات بين الملفات بأصفار لمحاذاة البيانات مع قطاعات الليزر (`2048 بايت`)، وتقوم أداة `extract-xiso` باستخراج البيانات الفعلية فقط.
* **فرق وحدات القياس:** تعرض بعض مديري الملفات حجم الملف بالنظام العشري ($1000^3$) بينما تحسب المجلدات بالنظام الثنائي ($1024^3$).

---

## ثانياً: سكربت إعادة التجميع إلى ملف XISO (نسخ ولصق دفعة واحدة)
بعد الانتهاء من التعديل على ملفات اللعبة داخل مجلد `Black_Xbox_Extracted` (مثل التعريب أو تعديل الملفات)، استخدم هذا السكربت لإعادة تجميع المجلد إلى ملف `.iso` بصيغة **XISO** نظيفة وجاهزة للعمل على المحاكيات (مثل **Xemu**) أو أجهزة Xbox المعدلة:

```bash
cat << 'EOF' > ~/repack_xiso_game.sh
#!/data/data/com.termux/files/usr/bin/bash
set -e

SRC_DIR="/storage/emulated/0/Download/logs/Black_Xbox_Extracted"
OUT_ISO="/storage/emulated/0/Download/logs/Black_Xbox_Repacked.iso"

echo "=========================================="
echo "1. التحقق من أداة extract-xiso..."
echo "=========================================="
if ! command -v extract-xiso >/dev/null 2>&1; then
    apt-get update -y
    apt-get install -y -o Dpkg::Options::="--force-confnew" git cmake make clang

    rm -rf ~/extract-xiso
    git clone --depth 1 https://github.com/XboxDev/extract-xiso.git ~/extract-xiso
    mkdir -p ~/extract-xiso/build
    cd ~/extract-xiso/build
    cmake .. -DCMAKE_C_FLAGS="-D__LINUX__"
    make -j$(nproc)
    cp extract-xiso "$PREFIX/bin/extract-xiso"
    chmod +x "$PREFIX/bin/extract-xiso"
    cd ~
    rm -rf ~/extract-xiso
fi

echo "=========================================="
echo "2. التحقق من مجلد ملفات اللعبة..."
echo "=========================================="
if [ ! -d "$SRC_DIR" ]; then
    echo "خطأ: المجلد غير موجود في المسار: $SRC_DIR"
    exit 1
fi

if [ ! -f "$SRC_DIR/default.xbe" ]; then
    echo "خطأ: ملف التشغيل الرئيسي default.xbe غير موجود داخل $SRC_DIR"
    echo "تأكد من أن المسار يشير إلى المجلد الجذري لملفات اللعبة."
    exit 1
fi

echo "=========================================="
echo "3. بدء إعادة تجميع اللعبة بصيغة XISO..."
echo "=========================================="
rm -f "$OUT_ISO"
extract-xiso -c "$SRC_DIR" "$OUT_ISO"

echo "=========================================="
echo "4. التحقق من ملف الـ ISO الناتج..."
echo "=========================================="
if [ -f "$OUT_ISO" ]; then
    ISO_SIZE=$(du -sh "$OUT_ISO" | cut -f1)
    echo "تمت إعادة التجميع بنجاح!"
    echo "ملف اللعبة الجديد: $OUT_ISO"
    echo "حجم الملف الناتج: $ISO_SIZE"
else
    echo "خطأ: فشل إنشاء ملف الـ ISO."
    exit 1
fi
echo "=========================================="
EOF
chmod +x ~/repack_xiso_game.sh && bash ~/repack_xiso_game.sh
```

> **ميزة تلقائية عند إعادة التجميع:** تقوم أداة `extract-xiso` تلقائياً بترقيع أعلام الوسائط داخل ملف `default.xbe` أثناء إنشاء الـ ISO لضمان إقلاع اللعبة دون أخطاء حماية القرص.

---

## ثالثاً: الأوامر السريعة للاستخدام المباشر مستقبلاً
بما أن أداة `extract-xiso` أصبحت مثبتة في النظام (`$PREFIX/bin/extract-xiso`)، يمكنك تنفيذ أي عملية مستقبلاً بأمر سطر واحد دون الحاجة إلى سكربت:

* **استخراج أي ملف Xbox ISO إلى مجلد:**
  ```bash
  extract-xiso -d "/مسار/مجلد/الاستخراج" "/مسار/ملف/اللعبة.iso"
  ```

* **إعادة تجميع أي مجلد لعبة إلى ملف XISO:**
  ```bash
  extract-xiso -c "/مسار/مجلد/اللعبة" "/مسار/الملف/الجديد.iso"
  ```

* **استعراض قائمة الملفات داخل ملف ISO دون استخراجه:**
  ```bash
  extract-xiso -l "/مسار/ملف/اللعبة.iso"
  ```

* **تحويل ملف ISO أصلي (Redump) ليعمل على محاكي Xemu مباشرة دون فكه:**
  ```bash
  extract-xiso -r "/مسار/ملف/اللعبة.iso"
  ```