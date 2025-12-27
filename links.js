// Website par data dikhane ke liye snippet
import { getDatabase, ref, onValue } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

const db = getDatabase();
const dealsRef = ref(db, 'amazonDeals/');

onValue(dealsRef, (snapshot) => {
    const data = snapshot.val();
    const AFFILIATE_TAG = data.affiliate_tag;
    const products = data.products;
    
    console.log("Tag:", AFFILIATE_TAG);
    console.log("Links:", products);
    
    // Yahan apna logic likhein links display karne ka
});
