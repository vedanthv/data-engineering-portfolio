"use client";

import { useState } from "react";

export default function Home() {

  const [product, setProduct] = useState("Pizza");
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState("");

  const placeOrder = async () => {

    const res = await fetch("/api/order", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        product,
        quantity
      })
    });

    const data = await res.json();
    setMessage(data.message);
  };

  return (

    <div style={styles.container}>

      <div style={styles.card}>

        <h1 style={styles.title}>🍕 Order Service</h1>

        <div style={styles.field}>
          <label style={styles.label}>Product</label>

          <select
            value={product}
            onChange={(e)=>setProduct(e.target.value)}
            style={styles.select}
            >
            <option>Pizza</option>
            <option>Burger</option>
            <option>Coffee</option>
          </select>
        </div>

        <div style={styles.field}>
          <label style={styles.label}>Quantity</label>

          <input
            type="number"
            min="1"
            value={quantity}
            onChange={(e)=>setQuantity(e.target.value)}
            style={styles.input}
          />
        </div>

        <button
          onClick={placeOrder}
          style={styles.button}
        >
          Place Order
        </button>

        {message && (
          <p style={styles.success}>
            {message}
          </p>
        )}

      </div>

    </div>

  );
}

const styles = {

  container: {
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "#000000",
    fontFamily: "Arial"
  },

  card: {
    background: "#ffffff",
    padding: "40px",
    borderRadius: "12px",
    width: "350px",
    border: "2px solid black",
    boxShadow: "none"
  },

  title: {
    textAlign: "center",
    marginBottom: "30px",
    color: "black"
  },

  field: {
    marginBottom: "20px",
    display: "flex",
    flexDirection: "column"
  },

  label: {
    marginBottom: "6px",
    fontWeight: "bold",
    color: "black"
  },

  select: {
    padding: "10px",
    borderRadius: "6px",
    border: "2px solid black",
    fontSize: "14px",
    color: "black",
    background: "white",
    outline: "none"
  },

  input: {
    padding: "10px",
    borderRadius: "6px",
    border: "2px solid black",
    fontSize: "14px",
    color: "black",
    background: "white",
    outline: "none"
  },

  button: {
    width: "100%",
    padding: "12px",
    background: "black",
    color: "white",
    border: "2px solid black",
    borderRadius: "6px",
    fontSize: "16px",
    cursor: "pointer"
  },

  success: {
    marginTop: "15px",
    textAlign: "center",
    color: "black",
    fontWeight: "bold"
  }

};