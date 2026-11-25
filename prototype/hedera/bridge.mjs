// CarbonTruth <-> Hedera bridge (testnet). Called by ct/hedera.py as:
//   node bridge.mjs <command> '<json-args>'      -> prints ONE json line on stdout
//
// Commands: setup | anchor | mint | burn
//   setup   create the HCS topic + HTS NFT collection once (ids cached in state.json)
//   anchor  submit a message to the HCS topic        {message}
//   mint    mint one VCC NFT serial                  {metadata}
//   burn    burn an NFT serial (retirement)          {serial}
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  Client, AccountId, PrivateKey, TopicCreateTransaction, TopicMessageSubmitTransaction,
  TokenCreateTransaction, TokenType, TokenSupplyType, TokenMintTransaction, TokenBurnTransaction,
} from "@hashgraph/sdk";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const STATE = path.join(HERE, "state.json");
const out = (o) => console.log(JSON.stringify(o));

function loadEnv() {
  for (const f of [path.join(HERE, ".env"), path.join(HERE, "..", ".env")]) {
    if (!fs.existsSync(f)) continue;
    for (const line of fs.readFileSync(f, "utf8").split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Z_]+)\s*=\s*(.*?)\s*$/);
      if (m && !(m[1] in process.env)) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
    }
  }
}
function parseKey(raw) {
  raw = raw.replace(/^0x/i, "");
  if (/^30[0-9a-f]{2}/i.test(raw) && raw.length > 70) return PrivateKey.fromStringDer(raw);
  return (process.env.HEDERA_KEY_TYPE || "ECDSA").toUpperCase() === "ED25519"
    ? PrivateKey.fromStringED25519(raw) : PrivateKey.fromStringECDSA(raw);
}
const readState = () => (fs.existsSync(STATE) ? JSON.parse(fs.readFileSync(STATE, "utf8")) : {});
const writeState = (s) => fs.writeFileSync(STATE, JSON.stringify(s, null, 2));
// HashScan wants 0.0.x-sec-nanos, the SDK prints 0.0.x@sec.nanos
const txUrl = (id) => "https://hashscan.io/testnet/transaction/" + id.replace("@", "-").replace(/\.(\d+)$/, "-$1");

async function main() {
  loadEnv();
  const [cmd, argJson] = process.argv.slice(2);
  const args = argJson ? JSON.parse(argJson) : {};
  if (!process.env.HEDERA_ACCOUNT_ID || !process.env.HEDERA_PRIVATE_KEY)
    return out({ ok: false, error: "HEDERA_ACCOUNT_ID / HEDERA_PRIVATE_KEY not set (see hedera/.env.example)" });

  const operatorId = AccountId.fromString(process.env.HEDERA_ACCOUNT_ID);
  const key = parseKey(process.env.HEDERA_PRIVATE_KEY);
  const client = Client.forTestnet().setOperator(operatorId, key);
  const st = readState();
  const done = async (tx) => {
    const resp = await tx.execute(client);
    const rc = await resp.getReceipt(client);
    const id = resp.transactionId.toString();
    return { rc, id, url: txUrl(id) };
  };

  try {
    if (cmd === "setup") {
      if (!st.topicId) {
        const r = await done(new TopicCreateTransaction().setTopicMemo("CarbonTruth VCC evidence log"));
        st.topicId = r.rc.topicId.toString();
      }
      if (!st.tokenId) {
        const r = await done(new TokenCreateTransaction()
          .setTokenName("CarbonTruth Verified Climate Claim").setTokenSymbol("VCC")
          .setTokenType(TokenType.NonFungibleUnique).setSupplyType(TokenSupplyType.Infinite)
          .setDecimals(0).setInitialSupply(0)
          .setTreasuryAccountId(operatorId).setSupplyKey(key.publicKey).setAdminKey(key.publicKey));
        st.tokenId = r.rc.tokenId.toString();
      }
      writeState(st);
      return out({ ok: true, ...st, topicUrl: `https://hashscan.io/testnet/topic/${st.topicId}`,
                   tokenUrl: `https://hashscan.io/testnet/token/${st.tokenId}` });
    }
    if (!st.topicId || !st.tokenId) return out({ ok: false, error: "run `setup` first" });

    if (cmd === "anchor") {
      const r = await done(new TopicMessageSubmitTransaction().setTopicId(st.topicId).setMessage(String(args.message)));
      return out({ ok: true, topicId: st.topicId, sequence: r.rc.topicSequenceNumber.toString(), tx: r.id, url: r.url });
    }
    if (cmd === "mint") {
      const meta = Buffer.from(String(args.metadata)).subarray(0, 100); // HTS metadata cap = 100 bytes
      const r = await done(new TokenMintTransaction().setTokenId(st.tokenId).addMetadata(meta));
      const serial = r.rc.serials[0].toString();
      return out({ ok: true, tokenId: st.tokenId, serial, tx: r.id, url: r.url,
                   nftUrl: `https://hashscan.io/testnet/token/${st.tokenId}/${serial}` });
    }
    if (cmd === "burn") {
      const r = await done(new TokenBurnTransaction().setTokenId(st.tokenId).setSerials([Number(args.serial)]));
      return out({ ok: true, tx: r.id, url: r.url });
    }
    return out({ ok: false, error: "unknown command " + cmd });
  } catch (e) {
    return out({ ok: false, error: String(e.message || e).split("\n")[0] });
  } finally { client.close(); }
}
main();
