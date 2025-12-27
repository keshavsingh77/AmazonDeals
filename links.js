<script type="module">
  import { initializeApp } from "https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js";
  import { getDatabase, ref, onValue } from "https://www.gstatic.com/firebasejs/12.5.0/firebase-database.js";

  const firebaseConfig = {
    apiKey: "AIzaSyCYqOxWY3ZVGTM6CELrwqQ3BXz79fRqHEQ",
    authDomain: "blog-post-51fbc.firebaseapp.com",
    databaseURL: "https://blog-post-51fbc-default-rtdb.firebaseio.com",
    projectId: "blog-post-51fbc",
    storageBucket: "blog-post-51fbc.firebasestorage.app",
    messagingSenderId: "195270065421",
    appId: "1:195270065421:web:347f9cb903f62719b6c444"
  };

  const app = initializeApp(firebaseConfig);
  const db = getDatabase(app);

  let AFFILIATE_TAG = "";
  let products = [];

  // Fetch Data from Firebase
  onValue(ref(db, '/'), (snapshot) => {
    const data = snapshot.val();
    if (data) {
      AFFILIATE_TAG = data.settings.affiliateTag;
      // Convert object to array
      products = data.products ? Object.values(data.products) : [];
      
      console.log("Current Tag:", AFFILIATE_TAG);
      console.log("Product Links:", products);

      // Aapka aage ka logic yahan likhein (e.g. products display karna)
      renderProducts();
    }
  });

  function renderProducts() {
      // Example: Links ko console mein print karna ya HTML mein dalna
      products.forEach(link => {
          // Link mein tag manually add karna ho toh:
          let finalLink = link.includes('?') ? `${link}&tag=${AFFILIATE_TAG}` : `${link}?tag=${AFFILIATE_TAG}`;
          console.log("Final URL:", finalLink);
      });
  }
</script>
