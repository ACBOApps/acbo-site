# Φόρμες του acbo.gr – οδηγός ρύθμισης

Η φόρμα επικοινωνίας και η εγγραφή σε ειδοποιήσεις στέλνουν email στο info@acbo.gr μέσω ενός μικρού προγράμματος στο Cloudflare (δωρεάν). Το site μένει στο GitHub Pages.

**Κανόνας ασφαλείας:** κανένα μυστικό (secret, κωδικός) δεν γράφεται στο GitHub, σε αρχεία ή σε συνομιλίες. Μπαίνουν μόνο στο Cloudflare.

## Α. Microsoft 365 (από τον διαχειριστή του M365)
1. **Γραμματοκιβώτιο αποστολής:** χρησιμοποιείται το κοινόχρηστο `social@acbo.gr`. Η εφαρμογή θα στέλνει από εκεί προς το info@acbo.gr. Σε κοινόχρηστο γραμματοκιβώτιο δεν γίνεται απευθείας σύνδεση με κωδικό, άρα είναι πιο ασφαλές.
2. **Εφαρμογή** στο Microsoft Entra: Entra admin center → App registrations → New registration (όνομα «ACBO forms», μόνο αυτός ο οργανισμός).
3. Στην εφαρμογή: API permissions → Add a permission → Microsoft Graph → **Application permissions** → `Mail.Send` → Grant admin consent.
4. Certificates & secrets → New client secret. **Σημειώστε πότε λήγει** (θα χρειαστεί ανανέωση).
5. **Περιορισμός πρόσβασης:** η εφαρμογή πρέπει να μπορεί να στέλνει μόνο από το `social@acbo.gr`, όχι από οποιοδήποτε γραμματοκιβώτιο. Στο Exchange Online PowerShell:
   - Δημιουργήστε μια mail-enabled security group (π.χ. `acbo-forms@acbo.gr`) με μέλος μόνο το γραμματοκιβώτιο `social@acbo.gr`.
   - `New-ApplicationAccessPolicy -AppId <Application (client) ID> -PolicyScopeGroupId acbo-forms@acbo.gr -AccessRight RestrictAccess -Description "ACBO forms"`
   - Έλεγχος: `Test-ApplicationAccessPolicy -Identity social@acbo.gr -AppId <client ID>` (πρέπει Granted) και με άλλο γραμματοκιβώτιο (πρέπει Denied).
   - Η Microsoft προωθεί σταδιακά το «RBAC for Applications» ως αντικαταστάτη της ApplicationAccessPolicy. Ο διαχειριστής μπορεί να επιλέξει όποιο ισχύει στον οργανισμό σας.
6. Κρατήστε τρία στοιχεία: **Directory (tenant) ID**, **Application (client) ID**, **Client secret**.

## Β. Cloudflare Turnstile (έλεγχος κατά του spam)
Cloudflare dashboard → Turnstile → Add widget. Hostnames: `acbo.gr`, `www.acbo.gr`, `acboapps.github.io`. Mode: Managed.
Θα πάρετε **Site Key** (δημόσιο, μπαίνει στο site) και **Secret Key** (μυστικό).

## Γ. Cloudflare Worker
1. Dashboard → Workers & Pages → Create → Worker, όνομα `acbo-forms` → Deploy.
2. Edit code → επικολλήστε όλο το περιεχόμενο του `form-worker.js` → Deploy.
3. Settings → Variables and secrets:
   - Secrets: `TURNSTILE_SECRET`, `MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET`.
   - Variables: `MAIL_TO` = `info@acbo.gr`, `MAIL_FROM` = `social@acbo.gr`.
4. Αντιγράψτε τη διεύθυνση του Worker (μορφή `https://acbo-forms.xxxx.workers.dev`).

## Δ. Σύνδεση με το site
Στείλτε μου **μόνο** τη διεύθυνση του Worker και το Site Key του Turnstile. Τα συνδέω στο site και δοκιμάζετε τη φόρμα από την προεπισκόπηση (acboapps.github.io).

## Δοκιμές κώδικα
`node worker/test.mjs`: ελέγχει όλους τους κανόνες (spam, ασφάλεια, αποστολή) χωρίς πραγματική αποστολή.

Ανέβασμα: γίνεται αυτόματα από το GitHub Actions (.github/workflows/deploy-worker.yml) όταν αλλάζει κάτι στον φάκελο worker/. Το κλειδί CLOUDFLARE_API_TOKEN (λήγει 15/11/2027) είναι στα Secrets του GitHub.
